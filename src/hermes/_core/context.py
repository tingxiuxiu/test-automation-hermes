import contextvars

from ..models.plugin import CaseModel, StepModel

current_case: contextvars.ContextVar[CaseModel | None] = contextvars.ContextVar(
    "current_case", default=None
)
current_step: contextvars.ContextVar[StepModel | None] = contextvars.ContextVar(
    "current_step", default=None
)
step_stack: contextvars.ContextVar[list[StepModel] | None] = contextvars.ContextVar(
    "step_stack", default=None
)


def init_context(case: CaseModel):
    current_case.set(case)
    current_step.set(None)
    step_stack.set([])


def get_current_case() -> CaseModel | None:
    return current_case.get()


def get_current_step() -> StepModel | None:
    return current_step.get()


def enter_step(step: StepModel):
    stack = step_stack.get()
    if stack:
        parent = stack[-1]
        parent.steps.append(step)
    else:
        case = current_case.get()
        if case:
            case.steps.append(step)

    stack.append(step)
    step_stack.set(stack)
    current_step.set(step)


def exit_step():
    stack = step_stack.get()
    if stack:
        stack.pop()
        step_stack.set(stack)
        if stack:
            current_step.set(stack[-1])
        else:
            current_step.set(None)


def clear_context():
    current_case.set(None)
    current_step.set(None)
    step_stack.set([])
