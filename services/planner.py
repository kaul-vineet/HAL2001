"""Planner task management service via Microsoft Graph."""

from msgraph import GraphServiceClient
from msgraph.generated.models.planner_task import PlannerTask
from rich.console import Console

console = Console()


class PlannerService:
    """Create and manage Planner tasks."""

    def __init__(self, client: GraphServiceClient):
        self.client = client

    async def list_my_tasks(self) -> list[dict]:
        """List Planner tasks assigned to the current user."""
        result = await self.client.me.planner.tasks.get()
        tasks = []
        if result and result.value:
            for task in result.value:
                tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "percent_complete": task.percent_complete,
                    "plan_id": task.plan_id,
                })
        return tasks

    async def create_task(
        self, plan_id: str, title: str, bucket_id: str = None
    ) -> str:
        """Create a new Planner task. Returns the task ID."""
        task = PlannerTask(plan_id=plan_id, title=title)
        if bucket_id:
            task.bucket_id = bucket_id
        result = await self.client.planner.tasks.post(task)
        return result.id if result else "unknown"

    async def complete_task(self, task_id: str, etag: str) -> bool:
        """Mark a Planner task as 100% complete."""
        from msgraph.generated.models.planner_task import PlannerTask

        update = PlannerTask(percent_complete=100)
        request_config = (
            lambda c: setattr(c.headers, "If-Match", etag)
        )
        await self.client.planner.tasks.by_planner_task_id(task_id).patch(
            update
        )
        return True

    async def list_plans(self, group_id: str) -> list[dict]:
        """List Planner plans for a group/team."""
        result = await self.client.groups.by_group_id(group_id).planner.plans.get()
        plans = []
        if result and result.value:
            for plan in result.value:
                plans.append({"id": plan.id, "title": plan.title})
        return plans
