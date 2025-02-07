import os
import time
from typing import Any, Dict, Union
from datetime import datetime, timedelta
from azure.cosmos.aio import ContainerProxy, CosmosClient
from auth.auth_utils import get_authenticated_user_details
from azure.identity.aio import AzureDeveloperCliCredential, ManagedIdentityCredential
from quart import Blueprint, current_app, jsonify, request

from config import (
    CONFIG_CHAT_HISTORY_COSMOS_ENABLED,
    CONFIG_COSMOS_HISTORY_CLIENT,
    CONFIG_COSMOS_HISTORY_CONTAINER,
    CONFIG_CREDENTIAL,
)
from decorators import authenticated
from error import error_response

chat_history_cosmosdb_bp = Blueprint("chat_history_cosmos", __name__, static_folder="static")


@chat_history_cosmosdb_bp.post("/chat_history")
@authenticated
async def post_chat_history(auth_claims: Dict[str, Any]):
    print("Received auth claims:", auth_claims)  # Add this line
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400
    container: ContainerProxy = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
    if not container:
        return jsonify({"error": "Chat history not enabled"}), 400
    
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    entra_oid = authenticated_user["user_principal_id"]
    
    #entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        request_json = await request.get_json()
        id = request_json.get("id")
        answers = request_json.get("answers")
        title = answers[0][0][:50] + "..." if len(answers[0][0]) > 50 else answers[0][0]
        timestamp = int(time.time() * 1000)

        await container.upsert_item(
            {"id": id, "entra_oid": entra_oid, "title": title, "answers": answers, "timestamp": timestamp}
        )

        return jsonify({}), 201
    except Exception as error:
        return error_response(error, "/chat_history")


@chat_history_cosmosdb_bp.post("/chat_history/items")
@authenticated
async def get_chat_history(auth_claims: Dict[str, Any]):
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400

    container: ContainerProxy = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
    if not container:
        return jsonify({"error": "Chat history not enabled"}), 400
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    entra_oid = authenticated_user["user_principal_id"]
    #entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        request_json = await request.get_json()
        count = request_json.get("count", 20)
        continuation_token = request_json.get("continuation_token")

        res = container.query_items(
            query="SELECT c.id, c.entra_oid, c.title, c.timestamp FROM c WHERE c.entra_oid = @entra_oid ORDER BY c.timestamp DESC",
            parameters=[dict(name="@entra_oid", value=entra_oid)],
            max_item_count=count,
        )

        # set the continuation token for the next page
        pager = res.by_page(continuation_token)

        # Get the first page, and the continuation token
        try:
            page = await pager.__anext__()
            continuation_token = pager.continuation_token  # type: ignore

            items = []
            async for item in page:
                items.append(
                    {
                        "id": item.get("id"),
                        "entra_oid": item.get("entra_oid"),
                        "title": item.get("title", "untitled"),
                        "timestamp": item.get("timestamp"),
                    }
                )

        # If there are no more pages, StopAsyncIteration is raised
        except StopAsyncIteration:
            items = []
            continuation_token = None

        return jsonify({"items": items, "continuation_token": continuation_token}), 200

    except Exception as error:
        return error_response(error, "/chat_history/items")

@chat_history_cosmosdb_bp.route("/check_rate_limit", methods=["GET"])
# In chat_history/cosmosdb.py

# Utility function (not a route)
async def perform_rate_limit_check(auth_claims: Dict[str, Any], authenticated_user=None):
    try:
        user_id = authenticated_user["user_principal_id"]
        container = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
        
        if not container:
            current_app.logger.error("Cosmos container not found in app config")
            return False

        exempt_user_ids = [
            "d938e63e-5abf-4fb4-810f-c2e20b525dbf"
        ]
        
        if user_id in exempt_user_ids:
            return True

        now = datetime.utcnow()
        time_window_ago = now - timedelta(days=20)
        
        time_window_ago_ms = int(time_window_ago.timestamp() * 1000)  # Convert to milliseconds
                # First, let's check what documents exist for this user
            
        # Then do the actual count
        time_window_ago = datetime.utcnow() - timedelta(days=7)
        time_window_ago_ms = int(time_window_ago.timestamp() * 1000)
        time_window_ago = datetime.utcnow() - timedelta(days=7)
        time_window_ago_seconds = int(time_window_ago.timestamp())
        
        count_query = """
            SELECT VALUE ARRAY_LENGTH(c.answers)
            FROM c
            WHERE c.entra_oid = @userId
            AND c._ts >= @timeWindow
        """
        
        parameters = [
            {"name": "@userId", "value": user_id},
            {"name": "@timeWindow", "value": time_window_ago_seconds}
        ]

        print(f"Checking rate limit for user {user_id}, time window {time_window_ago_seconds}")  # Debug
        
        total_answers = 0
        parameters = [
            {"name": "@userId", "value": user_id},
            {"name": "@timeWindow", "value": time_window_ago_seconds}
        ]

        async for count in container.query_items(query=count_query, parameters=parameters):
            if count:
                total_answers += count
        print(f"Total answers: {total_answers}")
        return total_answers <= 6, total_answers
       
    except Exception as e:
        current_app.logger.exception("Rate limit check failed: %s", str(e))
        return False, 0

# Route that uses the utility function
@chat_history_cosmosdb_bp.route("/check_rate_limit", methods=["GET"])
@authenticated
async def check_rate_limit(auth_claims: Dict[str, Any]):
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    is_allowed = await perform_rate_limit_check(authenticated_user)
    return jsonify({"allowed": is_allowed})

@chat_history_cosmosdb_bp.get("/chat_history/items/<item_id>")
@authenticated
async def get_chat_history_session(auth_claims: Dict[str, Any], item_id: str):
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400

    container: ContainerProxy = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
    if not container:
        return jsonify({"error": "Chat history not enabled"}), 400
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    entra_oid = authenticated_user["user_principal_id"]
    #entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        res = await container.read_item(item=item_id, partition_key=entra_oid)
        return (
            jsonify(
                {
                    "id": res.get("id"),
                    "entra_oid": res.get("entra_oid"),
                    "title": res.get("title", "untitled"),
                    "timestamp": res.get("timestamp"),
                    "answers": res.get("answers", []),
                }
            ),
            200,
        )
    except Exception as error:
        return error_response(error, f"/chat_history/items/{item_id}")


@chat_history_cosmosdb_bp.delete("/chat_history/items/<item_id>")
@authenticated
async def delete_chat_history_session(auth_claims: Dict[str, Any], item_id: str):
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400

    container: ContainerProxy = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
    if not container:
        return jsonify({"error": "Chat history not enabled"}), 400
    authenticated_user = get_authenticated_user_details(request_headers=request.headers)
    entra_oid = authenticated_user["user_principal_id"]
    #entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        await container.delete_item(item=item_id, partition_key=entra_oid)
        return jsonify({}), 204
    except Exception as error:
        return error_response(error, f"/chat_history/items/{item_id}")


@chat_history_cosmosdb_bp.before_app_serving
async def setup_clients():
    USE_CHAT_HISTORY_COSMOS = os.getenv("USE_CHAT_HISTORY_COSMOS", "").lower() == "true"
    AZURE_COSMOSDB_ACCOUNT = os.getenv("AZURE_COSMOSDB_ACCOUNT")
    AZURE_CHAT_HISTORY_DATABASE = os.getenv("AZURE_CHAT_HISTORY_DATABASE")
    AZURE_CHAT_HISTORY_CONTAINER = os.getenv("AZURE_CHAT_HISTORY_CONTAINER")

    azure_credential: Union[AzureDeveloperCliCredential, ManagedIdentityCredential] = current_app.config[
        CONFIG_CREDENTIAL
    ]

    if USE_CHAT_HISTORY_COSMOS:
        current_app.logger.info("USE_CHAT_HISTORY_COSMOS is true, setting up CosmosDB client")
        if not AZURE_COSMOSDB_ACCOUNT:
            raise ValueError("AZURE_COSMOSDB_ACCOUNT must be set when USE_CHAT_HISTORY_COSMOS is true")
        if not AZURE_CHAT_HISTORY_DATABASE:
            raise ValueError("AZURE_CHAT_HISTORY_DATABASE must be set when USE_CHAT_HISTORY_COSMOS is true")
        if not AZURE_CHAT_HISTORY_CONTAINER:
            raise ValueError("AZURE_CHAT_HISTORY_CONTAINER must be set when USE_CHAT_HISTORY_COSMOS is true")
        cosmos_client = CosmosClient(
            url=f"https://{AZURE_COSMOSDB_ACCOUNT}.documents.azure.com:443/", credential=azure_credential
        )
        cosmos_db = cosmos_client.get_database_client(AZURE_CHAT_HISTORY_DATABASE)
        cosmos_container = cosmos_db.get_container_client(AZURE_CHAT_HISTORY_CONTAINER)

        current_app.config[CONFIG_COSMOS_HISTORY_CLIENT] = cosmos_client
        current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER] = cosmos_container


@chat_history_cosmosdb_bp.after_app_serving
async def close_clients():
    if current_app.config.get(CONFIG_COSMOS_HISTORY_CLIENT):
        cosmos_client: CosmosClient = current_app.config[CONFIG_COSMOS_HISTORY_CLIENT]
        await cosmos_client.close()
