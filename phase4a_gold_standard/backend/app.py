"""FastAPI adapter for the Phase 4a human-review backend."""

from __future__ import annotations

import hmac
from pathlib import Path
from typing import Any

from fastapi import Body, Depends, FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .errors import (
    AuthenticationError,
    BackendError,
    PermissionDeniedError,
    ValidationError,
)
from .security import AuthenticatedUser, sign_cookie, unsign_cookie
from .service import AnnotationService, ServiceSettings


class LoginBody(BaseModel):
    username: str
    password: str


class AnnotationBody(BaseModel):
    annotation: dict[str, Any] = Field(default_factory=dict)
    expected_version: int = Field(ge=0)


class SkipBody(BaseModel):
    reason: str
    notes: str | None = None
    expected_version: int = Field(ge=0)


class ResumeBody(BaseModel):
    expected_version: int = Field(ge=0)


class UserBody(BaseModel):
    username: str
    display_name: str
    password: str
    role: str = "reviewer"
    allowed_languages: list[str] | None = None
    active: bool = True


def create_app(
    settings: ServiceSettings | None = None,
    *,
    service: AnnotationService | None = None,
) -> FastAPI:
    service = service or AnnotationService(settings)
    settings = service.settings
    application = FastAPI(
        title="FEATS Phase 4a Review API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    application.state.annotation_service = service

    @application.exception_handler(BackendError)
    async def backend_error_handler(
        _request: Request, error: BackendError
    ) -> JSONResponse:
        detail = {
            "code": error.code,
            "message": error.message,
            "details": error.details,
        }
        return JSONResponse(
            status_code=error.status_code,
            content={"code": error.code, "detail": detail},
        )

    @application.exception_handler(RequestValidationError)
    async def request_validation_handler(
        _request: Request, error: RequestValidationError
    ) -> JSONResponse:
        detail = {
            "code": "request_validation_error",
            "message": "the request body or parameters are invalid",
            "details": {"errors": error.errors()},
        }
        return JSONResponse(
            status_code=422,
            content={"code": detail["code"], "detail": detail},
        )

    def session_token(request: Request) -> str:
        cookie = request.cookies.get(settings.session_cookie)
        token = unsign_cookie(cookie, settings.session_secret) if cookie else None
        if token is None:
            raise AuthenticationError("a valid signed session cookie is required")
        return token

    def current_user(request: Request) -> AuthenticatedUser:
        token = session_token(request)
        user = service.resolve_session(token)
        request.state.session_token = token
        request.state.user = user
        return user

    def csrf_user(
        request: Request, user: AuthenticatedUser = Depends(current_user)
    ) -> AuthenticatedUser:
        supplied = request.headers.get("X-CSRF-Token", "")
        if not supplied or not hmac.compare_digest(supplied, user.csrf_token):
            raise PermissionDeniedError("the CSRF token is missing or invalid")
        return user

    def request_context(request: Request) -> dict[str, str | None]:
        forwarded = request.headers.get("x-forwarded-for")
        remote = (
            forwarded.split(",", 1)[0].strip()
            if forwarded
            else request.client.host if request.client else None
        )
        return {
            "request_id": request.headers.get("x-request-id"),
            "remote_addr": remote,
        }

    @application.get("/api/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "campaign_id": settings.campaign_id}

    @application.post("/api/auth/login")
    def login(body: LoginBody, request: Request, response: Response) -> dict[str, Any]:
        token, user = service.login(
            body.username,
            body.password,
            remote_addr=request_context(request)["remote_addr"],
        )
        signed = sign_cookie(token, settings.session_secret)
        response.set_cookie(
            settings.session_cookie,
            signed,
            max_age=settings.session_seconds,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="strict",
            path="/",
        )
        response.set_cookie(
            settings.csrf_cookie,
            user.csrf_token,
            max_age=settings.session_seconds,
            httponly=False,
            secure=settings.cookie_secure,
            samesite="strict",
            path="/",
        )
        return {
            "user": service.user_payload(user),
            "csrf_token": user.csrf_token,
        }

    @application.get("/api/auth/me")
    def me(user: AuthenticatedUser = Depends(current_user)) -> dict[str, Any]:
        return {
            "user": service.user_payload(user),
            "csrf_token": user.csrf_token,
        }

    @application.post("/api/auth/logout")
    def logout(
        request: Request,
        response: Response,
        user: AuthenticatedUser = Depends(csrf_user),
    ) -> dict[str, bool]:
        service.logout(request.state.session_token, user)
        response.delete_cookie(settings.session_cookie, path="/")
        response.delete_cookie(settings.csrf_cookie, path="/")
        return {"ok": True}

    @application.get("/api/me/progress")
    def my_progress(user: AuthenticatedUser = Depends(current_user)) -> dict[str, Any]:
        return {"progress": service.my_progress(user)}

    @application.get("/api/tasks/next")
    def next_task(
        request: Request, user: AuthenticatedUser = Depends(current_user)
    ) -> dict[str, Any]:
        task = service.claim_next(user, **request_context(request))
        return {"task": task}

    @application.get("/api/tasks/{task_id}")
    def get_task(
        task_id: str, user: AuthenticatedUser = Depends(current_user)
    ) -> dict[str, Any]:
        return {"task": service.get_task(task_id, user)}

    @application.post("/api/tasks/{task_id}/lease")
    def renew_lease(
        task_id: str, user: AuthenticatedUser = Depends(csrf_user)
    ) -> dict[str, Any]:
        service.require_reviewer(user)
        service.get_task(task_id, user)
        return service.database.renew_lease(task_id, reviewer_id=user.user_id)

    @application.patch("/api/annotations/{task_id}/draft")
    def save_draft(
        task_id: str,
        body: AnnotationBody,
        request: Request,
        user: AuthenticatedUser = Depends(csrf_user),
    ) -> dict[str, Any]:
        annotation = service.save(
            task_id,
            user,
            annotation=body.annotation,
            expected_version=body.expected_version,
            **request_context(request),
        )
        return {"annotation": annotation}

    @application.post("/api/annotations/{task_id}/submit")
    def submit(
        task_id: str,
        body: AnnotationBody,
        request: Request,
        user: AuthenticatedUser = Depends(csrf_user),
    ) -> dict[str, Any]:
        annotation = service.save(
            task_id,
            user,
            annotation=body.annotation,
            expected_version=body.expected_version,
            submit=True,
            **request_context(request),
        )
        return {"annotation": annotation}

    @application.post("/api/annotations/{task_id}/skip")
    def skip(
        task_id: str,
        body: SkipBody,
        request: Request,
        user: AuthenticatedUser = Depends(csrf_user),
    ) -> dict[str, Any]:
        annotation = service.skip(
            task_id,
            user,
            reason=body.reason,
            notes=body.notes,
            expected_version=body.expected_version,
            **request_context(request),
        )
        return {"annotation": annotation}

    @application.post("/api/annotations/{task_id}/resume")
    def resume(
        task_id: str,
        body: ResumeBody,
        request: Request,
        user: AuthenticatedUser = Depends(csrf_user),
    ) -> dict[str, Any]:
        task = service.resume(
            task_id,
            user,
            expected_version=body.expected_version,
            **request_context(request),
        )
        return {"task": task}

    @application.get("/api/annotations/mine")
    def list_mine(
        states: list[str] = Query(default=["draft", "skipped"]),
        user: AuthenticatedUser = Depends(current_user),
    ) -> dict[str, Any]:
        service.require_reviewer(user)
        return {"annotations": service.database.list_mine(user.user_id, states=states)}

    @application.post("/api/admin/users")
    def create_user(
        body: UserBody, user: AuthenticatedUser = Depends(csrf_user)
    ) -> dict[str, Any]:
        created = service.create_user(
            username=body.username,
            display_name=body.display_name,
            password=body.password,
            role=body.role,
            allowed_languages=body.allowed_languages,
            active=body.active,
            actor=user,
        )
        return {"user": service.user_payload(created)}

    @application.post("/api/admin/tasks/import")
    def import_tasks(
        payload: Any = Body(...),
        user: AuthenticatedUser = Depends(csrf_user),
    ) -> dict[str, Any]:
        if isinstance(payload, dict):
            records = payload.get("tasks")
        else:
            records = payload
        if not isinstance(records, list):
            raise ValidationError("import body must be a task list or an object with tasks")
        return {"import": service.import_tasks(records, actor=user)}

    @application.get("/api/admin/progress")
    def admin_progress(
        user: AuthenticatedUser = Depends(current_user),
    ) -> dict[str, Any]:
        return {"progress": service.admin_progress(user)}

    @application.get("/api/admin/export")
    def export(
        format: str = Query(default="jsonl", pattern="^(jsonl|csv)$"),
        user: AuthenticatedUser = Depends(current_user),
    ) -> PlainTextResponse:
        media_type = "application/x-ndjson" if format == "jsonl" else "text/csv"
        suffix = "jsonl" if format == "jsonl" else "csv"
        return PlainTextResponse(
            service.export(user, format=format),
            media_type=media_type,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="phase4a-{settings.campaign_id}.{suffix}"'
                )
            },
        )

    @application.get("/api/admin/report")
    def report(user: AuthenticatedUser = Depends(current_user)) -> dict[str, Any]:
        return {"report": service.report(user)}

    @application.get("/api/admin/tasks/{task_id}/revisions")
    def revisions(
        task_id: str, user: AuthenticatedUser = Depends(current_user)
    ) -> dict[str, Any]:
        return {"revisions": service.revisions(task_id, user)}

    @application.get("/api/admin/audit")
    def audit(
        task_id: str | None = None,
        limit: int = Query(default=1_000, ge=1, le=10_000),
        user: AuthenticatedUser = Depends(current_user),
    ) -> dict[str, Any]:
        return {
            "events": service.audit(user, task_id=task_id, limit=limit)
        }

    web_root = Path(__file__).resolve().parents[1] / "web"
    static_root = web_root / "static"
    template_root = web_root / "templates"
    if static_root.is_dir():
        application.mount("/static", StaticFiles(directory=static_root), name="static")
    if template_root.is_dir():
        templates = Jinja2Templates(directory=template_root)

        @application.get("/", response_class=HTMLResponse, include_in_schema=False)
        def index(request: Request) -> Any:
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={"request": request},
            )

    return application


app = create_app()
