"""SharePoint document monitoring service via Microsoft Graph."""

from msgraph import GraphServiceClient
from rich.console import Console

console = Console()


class SharePointService:
    """Monitor and browse SharePoint sites, libraries and documents."""

    def __init__(self, client: GraphServiceClient):
        self.client = client

    async def list_sites(self, search_query: str = "*") -> list[dict]:
        """Search for SharePoint sites."""
        from msgraph.generated.sites.sites_request_builder import SitesRequestBuilder

        query = SitesRequestBuilder.SitesRequestBuilderGetQueryParameters(
            search=search_query
        )
        config = SitesRequestBuilder.SitesRequestBuilderGetRequestConfiguration(
            query_parameters=query
        )
        result = await self.client.sites.get(request_configuration=config)
        sites = []
        if result and result.value:
            for site in result.value:
                sites.append({
                    "id": site.id,
                    "name": site.display_name,
                    "url": site.web_url,
                })
        return sites

    async def list_drive_items(
        self, site_id: str, folder_path: str = "root"
    ) -> list[dict]:
        """List files and folders in a SharePoint document library."""
        if folder_path == "root":
            result = await (
                self.client.sites.by_site_id(site_id)
                .drive.root.children.get()
            )
        else:
            result = await (
                self.client.sites.by_site_id(site_id)
                .drive.root.items_with_path(folder_path)
                .children.get()
            )
        items = []
        if result and result.value:
            for item in result.value:
                items.append({
                    "id": item.id,
                    "name": item.name,
                    "type": "folder" if item.folder else "file",
                    "size": item.size,
                    "modified": str(item.last_modified_date_time),
                    "url": item.web_url,
                })
        return items

    async def get_recent_changes(self, site_id: str) -> list[dict]:
        """Get recently modified items using delta query."""
        result = await (
            self.client.sites.by_site_id(site_id)
            .drive.root.children.get()
        )
        items = []
        if result and result.value:
            sorted_items = sorted(
                result.value,
                key=lambda x: x.last_modified_date_time or "",
                reverse=True,
            )
            for item in sorted_items[:20]:
                items.append({
                    "id": item.id,
                    "name": item.name,
                    "modified": str(item.last_modified_date_time),
                    "modified_by": (
                        item.last_modified_by.user.display_name
                        if item.last_modified_by and item.last_modified_by.user
                        else "unknown"
                    ),
                })
        return items

    async def search_documents(self, query: str) -> list[dict]:
        """Search across all SharePoint documents."""
        from msgraph.generated.search.query.query_post_request_body import (
            QueryPostRequestBody,
        )
        from msgraph.generated.models.search_request import SearchRequest
        from msgraph.generated.models.entity_type import EntityType

        search_request = SearchRequest(
            entity_types=[EntityType.DriveItem],
            query={"queryString": query},
        )
        request_body = QueryPostRequestBody(requests=[search_request])
        result = await self.client.search.query.post(request_body)
        docs = []
        if result and result.value:
            for response in result.value:
                if response.hits_containers:
                    for container in response.hits_containers:
                        if container.hits:
                            for hit in container.hits:
                                resource = hit.resource
                                docs.append({
                                    "name": getattr(resource, "name", "unknown"),
                                    "url": getattr(resource, "web_url", ""),
                                    "summary": hit.summary or "",
                                })
        return docs
