from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_role
from app.models import (
    Assessment,
    ClassGroup,
    Course,
    CourseDiscipline,
    Discipline,
    Enrollment,
    EnrollmentStatus,
    Organization,
    ProfessorClassLink,
    ProfessorRole,
    Role,
    Student,
    User,
)

router = APIRouter(prefix="/v1", tags=["academic"])


class AcademicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OrganizationInput(AcademicSchema):
    name: str


class OrganizationOut(OrganizationInput):
    id: str


class CourseInput(AcademicSchema):
    organization_id: str
    name: str
    code: str


class CourseOut(CourseInput):
    id: str


class DisciplineInput(AcademicSchema):
    organization_id: str
    name: str
    code: str


class DisciplineOut(DisciplineInput):
    id: str


class CourseDisciplineInput(AcademicSchema):
    course_id: str
    discipline_id: str


class CourseDisciplineOut(CourseDisciplineInput):
    id: str


class ClassGroupInput(AcademicSchema):
    course_discipline_id: str
    period: str
    code: str


class ClassGroupOut(ClassGroupInput):
    id: str


class ProfessorClassLinkInput(AcademicSchema):
    professor_id: str
    class_group_id: str
    role: ProfessorRole
    active: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ProfessorClassLinkUpdate(AcademicSchema):
    role: ProfessorRole | None = None
    active: bool | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ProfessorClassLinkOut(ProfessorClassLinkInput):
    id: str


class StudentInput(AcademicSchema):
    organization_id: str
    name: str
    external_id: str


class StudentOut(StudentInput):
    id: str


class EnrollmentInput(AcademicSchema):
    class_group_id: str
    student_id: str
    status: EnrollmentStatus = EnrollmentStatus.ACTIVE
    enrolled_at: datetime | None = None
    ended_at: datetime | None = None


class EnrollmentUpdate(AcademicSchema):
    status: EnrollmentStatus | None = None
    enrolled_at: datetime | None = None
    ended_at: datetime | None = None


class EnrollmentOut(AcademicSchema):
    id: str
    class_group_id: str
    student_id: str
    status: EnrollmentStatus
    enrolled_at: datetime
    ended_at: datetime | None


class AssessmentClassGroupInput(AcademicSchema):
    class_group_id: str


def active_link_condition(now: datetime | None = None):
    moment = now or datetime.utcnow()
    return and_(
        ProfessorClassLink.active.is_(True),
        or_(ProfessorClassLink.starts_at.is_(None), ProfessorClassLink.starts_at <= moment),
        or_(ProfessorClassLink.ends_at.is_(None), ProfessorClassLink.ends_at >= moment),
    )


def has_active_class_link(db: Session, user: User, class_group_id: str, *, responsible: bool = False) -> bool:
    if user.role == Role.ADMIN:
        return True
    query = db.query(ProfessorClassLink).filter(
        ProfessorClassLink.professor_id == user.id,
        ProfessorClassLink.class_group_id == class_group_id,
        active_link_condition(),
    )
    if responsible:
        query = query.filter(ProfessorClassLink.role == ProfessorRole.RESPONSIBLE)
    return query.first() is not None


def require_active_class_link(db: Session, user: User, class_group_id: str, *, responsible: bool = False) -> None:
    if not has_active_class_link(db, user, class_group_id, responsible=responsible):
        raise HTTPException(status_code=403, detail="Vínculo ativo com a turma é obrigatório.")


def require_assessment_mutation(db: Session, user: User, assessment: Assessment) -> None:
    if user.role == Role.ADMIN:
        return
    if assessment.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Sem permissão sobre esta avaliação.")
    if assessment.class_group_id is not None:
        require_active_class_link(db, user, assessment.class_group_id)


def _get(db: Session, model, resource_id: str):
    item = db.get(model, resource_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")
    return item


def _commit(db: Session, item, duplicate_message: str = "Conflito de integridade."):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=duplicate_message) from exc
    db.refresh(item)
    return item


def _update(item, payload: BaseModel) -> None:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)


def _delete(db: Session, item) -> Response:
    try:
        db.delete(item)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Recurso possui dependências.") from exc
    return Response(status_code=204)


def _admin(user: User) -> None:
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Somente administradores.")


def _active_class_ids(db: Session, user: User):
    return db.query(ProfessorClassLink.class_group_id).filter(
        ProfessorClassLink.professor_id == user.id, active_link_condition()
    )


def _organization_ids_for_user(db: Session, user: User):
    return (
        db.query(Course.organization_id)
        .join(CourseDiscipline, CourseDiscipline.course_id == Course.id)
        .join(ClassGroup, ClassGroup.course_discipline_id == CourseDiscipline.id)
        .filter(ClassGroup.id.in_(_active_class_ids(db, user)))
    )


@router.get("/organizations", response_model=list[OrganizationOut])
def list_organizations(db: Session = Depends(get_db), user: User = Depends(require_role("professor", "admin"))):
    query = db.query(Organization)
    if user.role == Role.PROFESSOR:
        query = query.filter(Organization.id.in_(_organization_ids_for_user(db, user)))
    return query.all()


@router.post("/organizations", response_model=OrganizationOut, status_code=201)
def create_organization(
    payload: OrganizationInput, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))
):
    item = Organization(**payload.model_dump())
    db.add(item)
    return _commit(db, item)


@router.get("/organizations/{resource_id}", response_model=OrganizationOut)
def get_organization(
    resource_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("professor", "admin"))
):
    query = db.query(Organization).filter(Organization.id == resource_id)
    if user.role == Role.PROFESSOR:
        query = query.filter(Organization.id.in_(_organization_ids_for_user(db, user)))
    item = query.first()
    if item is None:
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")
    return item


@router.patch("/organizations/{resource_id}", response_model=OrganizationOut)
def update_organization(
    resource_id: str,
    payload: OrganizationInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    item = _get(db, Organization, resource_id)
    _update(item, payload)
    return _commit(db, item)


@router.delete("/organizations/{resource_id}", status_code=204)
def delete_organization(resource_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))):
    return _delete(db, _get(db, Organization, resource_id))


def _register_admin_crud(path: str, model, input_schema, output_schema, scope_filter):
    async def list_items(db: Session = Depends(get_db), user: User = Depends(require_role("professor", "admin"))):
        query = db.query(model)
        if user.role == Role.PROFESSOR:
            query = scope_filter(query, db, user)
        return query.all()

    async def create_item(
        payload: input_schema, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))
    ):
        item = model(**payload.model_dump())
        db.add(item)
        return _commit(db, item)

    async def get_item(
        resource_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("professor", "admin"))
    ):
        query = db.query(model)
        if user.role == Role.PROFESSOR:
            query = scope_filter(query, db, user)
        item = query.filter(model.id == resource_id).first()
        if item is None:
            raise HTTPException(status_code=404, detail="Recurso não encontrado.")
        return item

    async def update_item(
        resource_id: str,
        payload: input_schema,
        db: Session = Depends(get_db),
        user: User = Depends(require_role("admin")),
    ):
        item = _get(db, model, resource_id)
        _update(item, payload)
        return _commit(db, item)

    async def delete_item(resource_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))):
        return _delete(db, _get(db, model, resource_id))

    names = model.__name__.lower()
    router.add_api_route(path, list_items, methods=["GET"], response_model=list[output_schema], name=f"list_{names}")
    router.add_api_route(
        path, create_item, methods=["POST"], response_model=output_schema, status_code=201, name=f"create_{names}"
    )
    router.add_api_route(
        f"{path}/{{resource_id}}", get_item, methods=["GET"], response_model=output_schema, name=f"get_{names}"
    )
    router.add_api_route(
        f"{path}/{{resource_id}}", update_item, methods=["PATCH"], response_model=output_schema, name=f"update_{names}"
    )
    router.add_api_route(
        f"{path}/{{resource_id}}", delete_item, methods=["DELETE"], status_code=204, name=f"delete_{names}"
    )


def _course_scope(query, db, user):
    return query.filter(Course.organization_id.in_(_organization_ids_for_user(db, user)))


def _discipline_scope(query, db, user):
    return query.filter(Discipline.organization_id.in_(_organization_ids_for_user(db, user)))


def _association_scope(query, db, user):
    return (
        query.join(ClassGroup, ClassGroup.course_discipline_id == CourseDiscipline.id)
        .filter(ClassGroup.id.in_(_active_class_ids(db, user)))
        .distinct()
    )


def _class_scope(query, db, user):
    return query.filter(ClassGroup.id.in_(_active_class_ids(db, user)))


_register_admin_crud("/courses", Course, CourseInput, CourseOut, _course_scope)
_register_admin_crud("/disciplines", Discipline, DisciplineInput, DisciplineOut, _discipline_scope)
_register_admin_crud(
    "/course-disciplines", CourseDiscipline, CourseDisciplineInput, CourseDisciplineOut, _association_scope
)
_register_admin_crud("/class-groups", ClassGroup, ClassGroupInput, ClassGroupOut, _class_scope)


@router.get("/professor-class-links", response_model=list[ProfessorClassLinkOut])
def list_links(db: Session = Depends(get_db), user: User = Depends(require_role("professor", "admin"))):
    query = db.query(ProfessorClassLink)
    if user.role == Role.PROFESSOR:
        query = query.filter(ProfessorClassLink.professor_id == user.id)
    return query.all()


@router.post("/professor-class-links", response_model=ProfessorClassLinkOut, status_code=201)
def create_link(
    payload: ProfessorClassLinkInput, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))
):
    professor = _get(db, User, payload.professor_id)
    if professor.role != Role.PROFESSOR:
        raise HTTPException(status_code=422, detail="O usuário informado não é professor.")
    _get(db, ClassGroup, payload.class_group_id)
    item = ProfessorClassLink(**payload.model_dump())
    db.add(item)
    return _commit(db, item, "Vínculo duplicado.")


@router.get("/professor-class-links/{resource_id}", response_model=ProfessorClassLinkOut)
def get_link(resource_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("professor", "admin"))):
    query = db.query(ProfessorClassLink).filter(ProfessorClassLink.id == resource_id)
    if user.role == Role.PROFESSOR:
        query = query.filter(ProfessorClassLink.professor_id == user.id)
    item = query.first()
    if item is None:
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")
    return item


@router.patch("/professor-class-links/{resource_id}", response_model=ProfessorClassLinkOut)
def update_link(
    resource_id: str,
    payload: ProfessorClassLinkUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    item = _get(db, ProfessorClassLink, resource_id)
    _update(item, payload)
    return _commit(db, item)


@router.delete("/professor-class-links/{resource_id}", status_code=204)
def delete_link(resource_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))):
    return _delete(db, _get(db, ProfessorClassLink, resource_id))


def _student_scope(query, db, user):
    return (
        query.join(Enrollment, Enrollment.student_id == Student.id)
        .filter(Enrollment.class_group_id.in_(_active_class_ids(db, user)))
        .distinct()
    )


_register_admin_crud("/students", Student, StudentInput, StudentOut, _student_scope)


def _enrollment_scope(query, db, user):
    return query.filter(Enrollment.class_group_id.in_(_active_class_ids(db, user)))


@router.get("/enrollments", response_model=list[EnrollmentOut])
def list_enrollments(db: Session = Depends(get_db), user: User = Depends(require_role("professor", "admin"))):
    query = db.query(Enrollment)
    if user.role == Role.PROFESSOR:
        query = _enrollment_scope(query, db, user)
    return query.all()


@router.post("/enrollments", response_model=EnrollmentOut, status_code=201)
def create_enrollment(
    payload: EnrollmentInput, db: Session = Depends(get_db), user: User = Depends(require_role("professor", "admin"))
):
    class_query = db.query(ClassGroup).filter(ClassGroup.id == payload.class_group_id)
    if user.role == Role.PROFESSOR:
        class_query = class_query.filter(ClassGroup.id.in_(_active_class_ids(db, user)))
    if class_query.first() is None:
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")
    require_active_class_link(db, user, payload.class_group_id, responsible=True)
    _get(db, Student, payload.student_id)
    if (
        payload.status == EnrollmentStatus.ACTIVE
        and db.query(Enrollment)
        .filter_by(class_group_id=payload.class_group_id, student_id=payload.student_id, status=EnrollmentStatus.ACTIVE)
        .first()
    ):
        raise HTTPException(status_code=409, detail="Matrícula ativa duplicada.")
    values = payload.model_dump()
    if values["enrolled_at"] is None:
        values.pop("enrolled_at")
    item = Enrollment(**values)
    db.add(item)
    return _commit(db, item)


@router.get("/enrollments/{resource_id}", response_model=EnrollmentOut)
def get_enrollment(
    resource_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("professor", "admin"))
):
    query = db.query(Enrollment).filter(Enrollment.id == resource_id)
    if user.role == Role.PROFESSOR:
        query = _enrollment_scope(query, db, user)
    item = query.first()
    if item is None:
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")
    return item


@router.patch("/enrollments/{resource_id}", response_model=EnrollmentOut)
def update_enrollment(
    resource_id: str,
    payload: EnrollmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    query = db.query(Enrollment).filter(Enrollment.id == resource_id)
    if user.role == Role.PROFESSOR:
        query = query.filter(
            Enrollment.class_group_id.in_(
                db.query(ProfessorClassLink.class_group_id).filter(
                    ProfessorClassLink.professor_id == user.id,
                    ProfessorClassLink.role == ProfessorRole.RESPONSIBLE,
                    active_link_condition(),
                )
            )
        )
    item = query.first()
    if item is None:
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")
    _update(item, payload)
    return _commit(db, item)


@router.delete("/enrollments/{resource_id}", status_code=204)
def delete_enrollment(resource_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))):
    return _delete(db, _get(db, Enrollment, resource_id))


@router.post("/assessments/{assessment_id}/class-group")
def attach_assessment_class_group(
    assessment_id: str,
    payload: AssessmentClassGroupInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("professor", "admin")),
):
    assessment_query = db.query(Assessment).filter(Assessment.id == assessment_id)
    if user.role == Role.PROFESSOR:
        assessment_query = assessment_query.filter(Assessment.owner_id == user.id)
    assessment = assessment_query.first()
    if assessment is None:
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")
    require_assessment_mutation(db, user, assessment)

    class_query = db.query(ClassGroup).filter(ClassGroup.id == payload.class_group_id)
    if user.role == Role.PROFESSOR:
        class_query = class_query.filter(ClassGroup.id.in_(_active_class_ids(db, user)))
    if class_query.first() is None:
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")
    assessment.class_group_id = payload.class_group_id
    return _commit(db, assessment)
