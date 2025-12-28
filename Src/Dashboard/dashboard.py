"""
Streamlit dashboard for Photo Factory monitoring.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import docker
import streamlit as st
from sqlalchemy import func
from streamlit_autorefresh import st_autorefresh

from Src.Shared.database import get_db_session, check_database_connection, init_database
from Src.Shared.models import MediaAsset, SystemStatus
from Src.Shared.heartbeat_service import HeartbeatService

logger = logging.getLogger("dashboard")

# Configure Streamlit page
st.set_page_config(
    page_title="Photo Factory Dashboard",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Docker client
try:
    docker_client = docker.from_env()
    DOCKER_AVAILABLE = True
except Exception as e:
    logger.warning(f"Docker client unavailable: {e}")
    docker_client = None
    DOCKER_AVAILABLE = False


@st.cache_data(ttl=5)  # Cache for 5 seconds
def get_container_status(container_name: str) -> Optional[dict]:
    """
    Get real-time container status from Docker.
    
    Args:
        container_name: Name of the container
    
    Returns:
        Dictionary with status info or None if unavailable
    """
    if not DOCKER_AVAILABLE:
        return None
    
    try:
        container = docker_client.containers.get(container_name)
        return {
            "status": container.status,
            "health": container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown"),
            "running": container.status == "running",
        }
    except docker.errors.NotFound:
        return {"status": "not_found", "health": "unknown", "running": False}
    except Exception as e:
        logger.error(f"Error getting container status: {e}")
        return None


@st.cache_data(ttl=5)  # Cache for 5 seconds to reduce DB load
def get_librarian_heartbeat() -> Optional[dict]:
    """Get latest heartbeat from librarian service."""
    try:
        with get_db_session() as session:
            status = session.query(SystemStatus).filter(
                SystemStatus.service_name == "librarian"
            ).first()
            if status:
                # Access all attributes while still in session context
                return {
                    "last_heartbeat": status.last_heartbeat,
                    "status": status.status,
                    "current_task": status.current_task,
                    "updated_at": status.updated_at,
                }
            return None
    except Exception as e:
        logger.error(f"Error getting heartbeat: {e}")
        return None


@st.cache_data(ttl=10)  # Cache for 10 seconds
def get_total_assets() -> int:
    """Get total number of processed assets."""
    try:
        with get_db_session() as session:
            count = session.query(func.count(MediaAsset.id)).scalar()
            return count or 0
    except Exception as e:
        logger.error(f"Error getting total assets: {e}")
        return 0


@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_assets_last_hour() -> int:
    """Get number of assets processed in the last hour."""
    try:
        with get_db_session() as session:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            count = session.query(func.count(MediaAsset.id)).filter(
                MediaAsset.ingested_at >= one_hour_ago
            ).scalar()
            return count or 0
    except Exception as e:
        logger.error(f"Error getting assets last hour: {e}")
        return 0


@st.cache_data(ttl=5)  # Cache for 5 seconds
def get_recent_assets(limit: int = 10):
    """Get most recently ingested assets."""
    try:
        with get_db_session() as session:
            assets = session.query(MediaAsset).order_by(
                MediaAsset.ingested_at.desc()
            ).limit(limit).all()
            # Convert to dicts to avoid DetachedInstanceError
            return [
                {
                    "id": str(asset.id),
                    "original_name": asset.original_name,
                    "final_path": asset.final_path,
                    "captured_at": asset.captured_at,
                    "ingested_at": asset.ingested_at,
                    "size_bytes": asset.size_bytes,
                }
                for asset in assets
            ]
    except Exception as e:
        logger.error(f"Error getting recent assets: {e}")
        return []


def get_remaining_files() -> Optional[int]:
    """
    Get count of files remaining in Photos_Inbox.
    
    Returns None if calculation is not feasible without major architectural changes.
    """
    # This would require scanning the inbox directory
    # For now, return None to indicate it's not available
    return None


def get_librarian_queue_length() -> Optional[int]:
    """
    Get approximate queue length for librarian service.
    This would require the librarian to track pending files.
    For now, we can estimate by checking files in Photos_Inbox.
    """
    # This would require access to the file system or librarian's internal state
    # For now, return None to indicate it's not available
    return None


@st.cache_data(ttl=5)  # Cache for 5 seconds
def get_service_heartbeat(service_name: str) -> Optional[dict]:
    """Get latest heartbeat from a specific service."""
    try:
        with get_db_session() as session:
            status = session.query(SystemStatus).filter(
                SystemStatus.service_name == service_name
            ).first()
            if status:
                # Access all attributes while still in session context
                return {
                    "last_heartbeat": status.last_heartbeat,
                    "status": status.status,
                    "current_task": status.current_task,
                    "updated_at": status.updated_at,
                }
            return None
    except Exception as e:
        logger.error(f"Error getting heartbeat for {service_name}: {e}")
        return None


@st.cache_data(ttl=5)  # Cache for 5 seconds
def get_all_services_status() -> list:
    """Get status for all available services."""
    services_status = []
    
    if not DOCKER_AVAILABLE:
        return services_status
    
    available_services = get_available_services()
    
    # Map container names to service names in database
    # Services without heartbeats are mapped to None (they'll still appear in dashboard)
    container_to_service_map = {
        # Photo Factory core services (with heartbeats)
        "librarian": "librarian",
        "dashboard": "dashboard",
        "factory_postgres": "factory-db",
        "syncthing": "syncthing",
        "service_monitor": None,  # Monitor doesn't have its own heartbeat
        # Immich services (no heartbeats, but should appear in dashboard)
        "immich_server": None,
        "immich_machine_learning": None,
        "immich_redis": None,
        "immich_postgres": None,
        # Other services
        "homepage": None,
    }
    
    for container_name in available_services:
        container_status = get_container_status(container_name)
        # Map container name to service name for heartbeat lookup
        service_name = container_to_service_map.get(container_name, container_name.split("_")[0] if "_" in container_name else container_name)
        heartbeat = get_service_heartbeat(service_name) if service_name else None
        
        status_info = {
            "name": container_name,  # Use container name for display
            "service_name": service_name,  # Service name in database
            "container_running": container_status["running"] if container_status else False,
            "container_health": container_status.get("health", "unknown") if container_status else "unknown",
            "heartbeat": heartbeat,
        }
        services_status.append(status_info)
    
    return services_status


@st.cache_data(ttl=30)  # Cache for 30 seconds (services don't change often)
def get_available_services() -> list:
    """Get list of available Docker services."""
    if not DOCKER_AVAILABLE:
        # Return known services even if Docker is unavailable
        return ["librarian", "dashboard", "factory_postgres", "syncthing", "service_monitor"]  # service_monitor is container_name
    
    try:
        # Get all containers - filter for Photo Factory services
        containers = docker_client.containers.list(all=True)
        service_names = []
        # ALL Photo Factory services - must include everything from docker-compose.yml
        known_services = [
            # Photo Factory core services
            "librarian", 
            "dashboard", 
            "factory-db", 
            "factory_postgres", 
            "syncthing", 
            "service_monitor",
            # Immich services
            "immich_server",
            "immich_machine_learning",
            "immich_redis",
            "immich_postgres",
            "homepage",
        ]
        
        # Also check image names for photo-factory prefix
        all_container_names = []
        for container in containers:
            name = container.name
            all_container_names.append(name)
            try:
                image_name = container.image.tags[0] if container.image.tags else ""
            except:
                image_name = ""
            
            # Check if it's a known service (exact match first, then substring) OR has photo-factory in image name OR container name
            is_known_service = name in known_services or any(known in name for known in known_services)
            has_photo_factory = (image_name and "photo-factory" in image_name.lower()) or "photo-factory" in name.lower()
            
            # Debug logging for service_monitor
            if "service" in name.lower() and "monitor" in name.lower():
                logger.info(f"Service discovery: name='{name}', image='{image_name}', is_known={is_known_service}, has_photo_factory={has_photo_factory}, will_add={is_known_service or has_photo_factory}")
            
            if is_known_service or has_photo_factory:
                service_names.append(name)
        
        # Explicitly add service_monitor if it exists in container list (regardless of other checks)
        if "service_monitor" in all_container_names:
            if "service_monitor" not in service_names:
                logger.warning(f"service_monitor found in containers but not added by discovery logic. Adding explicitly.")
                service_names.append("service_monitor")
        
        # Remove duplicates and sort
        result = sorted(list(set(service_names)))
        logger.info(f"Final service list: {result}")
        return result
    except Exception as e:
        logger.error(f"Error getting available services: {e}")
        # Return known services as fallback
        return ["librarian", "dashboard", "factory_postgres", "syncthing", "service_monitor", "immich_server", "immich_machine_learning", "immich_redis", "immich_postgres", "homepage"]


@st.cache_data(ttl=2)  # Cache for 2 seconds (logs change frequently)
def get_service_logs(service_name: str, tail: int = 100) -> str:
    """
    Get logs from a specific service.
    
    Args:
        service_name: Name of the Docker container/service
        tail: Number of lines to retrieve
    
    Returns:
        Logs as string, or empty string if error
    """
    if not DOCKER_AVAILABLE:
        return ""
    
    try:
        container = docker_client.containers.get(service_name)
        logs = container.logs(tail=tail, timestamps=True).decode("utf-8")
        return logs
    except docker.errors.NotFound:
        return f"[Service '{service_name}' not found]"
    except Exception as e:
        logger.error(f"Error fetching logs from {service_name}: {e}")
        return ""
        return f"[Error fetching logs from {service_name}: {e}]"


def get_all_logs(services: list, tail: int = 100) -> str:
    """
    Get and combine logs from all services.
    
    Args:
        services: List of service names
        tail: Number of lines per service
    
    Returns:
        Combined logs with service headers
    """
    all_logs = []
    
    for service in services:
        logs = get_service_logs(service, tail=tail)
        if logs:
            # Add service header
            all_logs.append(f"\n{'='*80}")
            all_logs.append(f"SERVICE: {service}")
            all_logs.append(f"{'='*80}\n")
            all_logs.append(logs)
    
    return "\n".join(all_logs)


# Initialize heartbeat service (runs in background thread)
# Use @st.cache_resource to ensure heartbeat persists across Streamlit reruns
_heartbeat_service_instance = None

@st.cache_resource
def _get_heartbeat_service():
    """
    Get or create heartbeat service for dashboard.
    
    Uses @st.cache_resource to ensure this only runs once and persists
    across Streamlit script reruns. This is critical because Streamlit
    reruns the entire script on every interaction, but we need the
    heartbeat thread to persist.
    """
    global _heartbeat_service_instance
    if _heartbeat_service_instance is not None:
        return _heartbeat_service_instance
    
    try:
        # Initialize database (ensures tables exist)
        init_database()
        
        # Start heartbeat service (5 minute interval)
        # Note: HeartbeatService now writes initial heartbeat immediately on start()
        heartbeat_service = HeartbeatService(service_name="dashboard", interval=300.0)
        heartbeat_service.set_current_task("Dashboard running")
        heartbeat_service.start()
        
        _heartbeat_service_instance = heartbeat_service
        logger.info("Dashboard heartbeat service started")
        return heartbeat_service
    except Exception as e:
        logger.error(f"Failed to initialize heartbeat: {e}", exc_info=True)
        return None

def _init_heartbeat():
    """Initialize heartbeat service (wrapper to ensure it's called)."""
    try:
        return _get_heartbeat_service()
    except Exception as e:
        # Fallback if @st.cache_resource fails (e.g., outside Streamlit context)
        logger.warning(f"@st.cache_resource failed, using fallback: {e}")
        global _heartbeat_service_instance
        if _heartbeat_service_instance is None:
            try:
                init_database()
                heartbeat_service = HeartbeatService(service_name="dashboard", interval=300.0)
                heartbeat_service.set_current_task("Dashboard running")
                heartbeat_service.start()
                _heartbeat_service_instance = heartbeat_service
                logger.info("Dashboard heartbeat service started (fallback)")
                return heartbeat_service
            except Exception as e2:
                logger.error(f"Fallback initialization failed: {e2}", exc_info=True)
                return None
        return _heartbeat_service_instance

def main():
    """Main dashboard function."""
    # Initialize heartbeat on first run (cached by @st.cache_resource)
    heartbeat_service = _init_heartbeat()
    if heartbeat_service is None:
        logger.warning("Dashboard heartbeat service failed to initialize")
    # Set page title and add CSS to reduce visual flash
    st.markdown(
        """
        <script>
        document.title = "Photo Factory Dashboard";
        </script>
        <style>
        /* Reduce visual flash during refresh with better transitions */
        .stApp {
            transition: opacity 0.2s ease-in-out;
        }
        /* Smooth transitions for metrics and dataframes */
        [data-testid="stMetricValue"],
        [data-testid="stDataFrame"],
        [data-testid="stCode"] {
            transition: opacity 0.15s ease-in-out;
        }
        /* Prevent layout shift during refresh */
        .element-container {
            min-height: 1px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.title("📸 Photo Factory Dashboard")
    
    # Service Selector at the top
    available_services = get_available_services()
    if available_services:
        service_options = ["All Services"] + available_services
        selected_service = st.selectbox(
            "🔍 **Select Service to View:**",
            options=service_options,
            index=0,
            key="service_selector"
        )
    else:
        selected_service = "All Services"
        st.warning("No services available")
    
    st.markdown("---")
    
    # Check database connection
    db_connected = check_database_connection()
    
    # Auto-refresh in sidebar (minimal)
    with st.sidebar:
        # Initialize session state (persists across reruns)
        if "auto_refresh_enabled" not in st.session_state:
            st.session_state.auto_refresh_enabled = True
        if "refresh_interval" not in st.session_state:
            st.session_state.refresh_interval = 10
        if "refresh_key_counter" not in st.session_state:
            st.session_state.refresh_key_counter = 0
        if "is_refreshing" not in st.session_state:
            st.session_state.is_refreshing = False
        
        auto_refresh = st.checkbox("Auto-refresh", value=st.session_state.auto_refresh_enabled, key="auto_refresh_checkbox")
        refresh_interval = st.slider("Interval (sec)", 5, 60, st.session_state.refresh_interval, key="refresh_interval_slider")
        
        # Check if interval changed - if so, increment counter to force refresh component restart
        if refresh_interval != st.session_state.get("last_refresh_interval", refresh_interval):
            st.session_state.refresh_key_counter += 1
        st.session_state.last_refresh_interval = refresh_interval
        
        # Update session state when values change
        st.session_state.auto_refresh_enabled = auto_refresh
        st.session_state.refresh_interval = refresh_interval
        
        if st.button("🔄 Refresh Now", key="refresh_button"):
            # Mark as refreshing and clear cache
            st.session_state.is_refreshing = True
            st.cache_data.clear()
            st.rerun()
        
        # Use streamlit-autorefresh for reliable auto-refresh
        if auto_refresh:
            st.info(f"🔄 Auto-refreshing every {refresh_interval}s")
            
            # Simple approach: always use fresh data, just show a subtle refresh indicator
            # The refresh happens so fast that preserving old state causes more problems
            st.session_state.is_refreshing = False  # Always use fresh data
            
            # Convert seconds to milliseconds for st_autorefresh
            # Use counter in key to force restart when interval changes
            st_autorefresh(
                interval=refresh_interval * 1000, 
                key=f"dashboard_refresh_{st.session_state.refresh_key_counter}"
            )
    
    # Show service-specific or all services data
    if selected_service == "All Services":
        # Show overview for all services
        st.subheader("System Overview")
        
        # Infrastructure status
        infra_col1, infra_col2 = st.columns(2)
        with infra_col1:
            db_status = "🟢 Connected" if db_connected else "🔴 Disconnected"
            st.write(f"**Database:** {db_status}")
        
        with infra_col2:
            docker_status = "🟢 Available" if DOCKER_AVAILABLE else "🔴 Unavailable"
            st.write(f"**Docker:** {docker_status}")
        
        st.markdown("---")
        
        # All Services Status
        st.subheader("All Services Status")
        
        # Always use fresh data - caching handles performance
        services_status = get_all_services_status()
        
        if services_status:
            # Create a table of all services
            try:
                import pandas as pd
            except ImportError:
                st.error("pandas not available")
                return
            
            status_data = []
            for svc in services_status:
                # Determine status indicator
                if svc["container_running"]:
                    if svc["container_health"] == "healthy":
                        status_indicator = "🟢 Healthy"
                    elif svc["container_health"] == "unhealthy":
                        status_indicator = "🔴 Unhealthy"
                    else:
                        status_indicator = f"🟡 {svc['container_health']}"
                else:
                    status_indicator = "🔴 Not Running"
                
                # Heartbeat info - always calculate fresh from current time
                # Format: <elapsed_time>s/<max_interval>s (e.g., 231s/300s or 56s/60s)
                heartbeat_info = "N/A"
                if svc["heartbeat"]:
                    # Map service names to their max expected intervals (in seconds)
                    service_max_intervals = {
                        "librarian": 60,      # Updates every 60 seconds
                        "dashboard": 300,     # Updates every 5 minutes
                        "factory-db": 300,    # Monitored every 5 minutes
                        "syncthing": 300,     # Monitored every 5 minutes
                    }
                    
                    # Get service name for interval lookup
                    service_name = svc.get("service_name")
                    container_name = svc["name"]
                    
                    # Determine max interval based on service name
                    if service_name and service_name in service_max_intervals:
                        max_interval = service_max_intervals[service_name]
                    elif container_name == "factory_postgres":
                        max_interval = 300  # factory-db
                    else:
                        max_interval = 300  # Default to 5 minutes
                    
                    time_since = datetime.now() - svc["heartbeat"]["last_heartbeat"]
                    seconds_ago = int(time_since.total_seconds())
                    
                    # Color logic relative to max_interval:
                    # - <= max_interval: green (within expected interval)
                    # - <= max_interval * 2: yellow (late but not critical)
                    # - > max_interval * 2: red (very late, critical)
                    if seconds_ago <= max_interval:
                        color = "🟢"
                    elif seconds_ago <= max_interval * 2:
                        color = "🟡"
                    else:
                        color = "🔴"
                    
                    # Format: "231s/300s ago" or "56s/60s ago"
                    heartbeat_info = f"{color} {seconds_ago}s/{max_interval}s ago"
                
                status_data.append({
                    "Service": svc["name"],
                    "Status": status_indicator,
                    "Heartbeat": heartbeat_info,
                    "Current Task": svc["heartbeat"].get("current_task", "N/A") if svc["heartbeat"] else "N/A",
                })
            
            df = pd.DataFrame(status_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No services found or Docker unavailable")
        
        st.markdown("---")
        
        # Overall Statistics - always use fresh data
        st.subheader("Overall Statistics")
        stats_container = st.container()
        with stats_container:
            col1, col2, col3, col4 = st.columns(4)
            
            # Always get fresh data - caching handles performance
            total_assets = get_total_assets()
            assets_last_hour = get_assets_last_hour()
            heartbeat = get_librarian_heartbeat()
            
            with col1:
                st.metric("Total Assets Secured", f"{total_assets:,}")
            
            with col2:
                st.metric("Processed Last Hour", f"{assets_last_hour:,}")
            
            with col3:
                remaining = get_remaining_files()
                if remaining is not None:
                    st.metric("Remaining in Inbox", f"{remaining:,}")
                else:
                    st.metric("Remaining in Inbox", "N/A")
            
            with col4:
                if heartbeat:
                    max_interval = 60  # Librarian updates every 60 seconds
                    time_since = datetime.now() - heartbeat["last_heartbeat"]
                    seconds_ago = int(time_since.total_seconds())
                    # Color logic relative to max_interval
                    if seconds_ago <= max_interval:
                        st.metric("Librarian Heartbeat", f"🟢 {seconds_ago}s/{max_interval}s ago")
                    elif seconds_ago <= max_interval * 2:
                        st.metric("Librarian Heartbeat", f"🟡 {seconds_ago}s/{max_interval}s ago")
                    else:
                        st.metric("Librarian Heartbeat", f"🔴 {seconds_ago}s/{max_interval}s ago")
                else:
                    st.metric("Librarian Heartbeat", "N/A")
        
        st.markdown("---")
        
        # Latest Processed Files - use empty container
        st.subheader("📁 Latest Processed Files")
        files_container = st.empty()
        recent_assets = get_recent_assets(limit=10)
        
        if recent_assets:
            try:
                import pandas as pd
            except ImportError:
                files_container.error("pandas not available")
            else:
                data = []
                for asset in recent_assets:
                    data.append({
                        "File": asset.get("original_name", "Unknown"),
                        "Size": f"{asset.get('size_bytes', 0) / 1024 / 1024:.2f} MB",
                        "Captured": asset.get("captured_at").strftime("%Y-%m-%d %H:%M") if asset.get("captured_at") else "N/A",
                        "Ingested": asset.get("ingested_at").strftime("%Y-%m-%d %H:%M:%S") if asset.get("ingested_at") else "N/A",
                        "Path": asset.get("final_path", "N/A")[:50] + "..." if len(asset.get("final_path", "")) > 50 else asset.get("final_path", "N/A"),
                    })
                
                df = pd.DataFrame(data)
                files_container.dataframe(df, use_container_width=True, hide_index=True)
        else:
            files_container.info("No files processed yet")
        
        st.markdown("---")
        
        # All Services Logs - use empty container
        st.subheader("📋 All Services Logs")
        logs_container = st.empty()
        if DOCKER_AVAILABLE and available_services:
            all_logs = get_all_logs(available_services, tail=50)
            if all_logs:
                log_lines = [line for line in all_logs.split('\n') if line.strip()]
                recent_logs = '\n'.join(log_lines[-100:])
                logs_container.code(recent_logs, language=None)
            else:
                logs_container.info("No logs available")
        else:
            logs_container.warning("Docker unavailable - cannot fetch logs")
    
    else:
        # Show service-specific data
        service_display_name = selected_service.replace("_", " ").replace("-", " ").title()
        st.subheader(f"📊 {service_display_name} Service Details")
        
        # Service Status
        container_status = get_container_status(selected_service)
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            if container_status:
                if container_status["running"]:
                    health = container_status.get("health", "unknown")
                    if health == "healthy":
                        st.success(f"🟢 Status: Running (Healthy)")
                    elif health == "unhealthy":
                        st.error(f"🔴 Status: Running (Unhealthy)")
                    else:
                        st.info(f"🟡 Status: Running ({health})")
                else:
                    st.error(f"🔴 Status: {container_status['status']}")
            else:
                st.warning("⚠️ Status unavailable")
        
        with status_col2:
            # Get heartbeat if available
            service_name_for_heartbeat = selected_service.split("_")[0] if "_" in selected_service else selected_service
            # Map container names to service names
            if selected_service == "factory_postgres":
                service_name_for_heartbeat = "factory-db"
            elif selected_service == "syncthing":
                service_name_for_heartbeat = "syncthing"  # Explicit mapping for syncthing
            
            heartbeat = get_service_heartbeat(service_name_for_heartbeat)
            
            # Map service names to their max expected intervals (in seconds)
            service_max_intervals = {
                "librarian": 60,      # Updates every 60 seconds
                "dashboard": 300,     # Updates every 5 minutes
                "factory-db": 300,    # Monitored every 5 minutes
                "syncthing": 300,     # Monitored every 5 minutes
            }
            
            if heartbeat:
                max_interval = service_max_intervals.get(service_name_for_heartbeat, 300)  # Default to 5 minutes
                time_since = datetime.now() - heartbeat["last_heartbeat"]
                seconds_ago = int(time_since.total_seconds())
                # Color logic relative to max_interval
                if seconds_ago <= max_interval:
                    st.success(f"💓 Heartbeat: {seconds_ago}s/{max_interval}s ago")
                elif seconds_ago <= max_interval * 2:
                    st.warning(f"💓 Heartbeat: {seconds_ago}s/{max_interval}s ago")
                else:
                    st.error(f"💓 Heartbeat: {seconds_ago}s/{max_interval}s ago")
                
                if heartbeat.get("current_task"):
                    st.caption(f"Current Task: {heartbeat['current_task']}")
            else:
                st.info("No heartbeat data available")
        
        st.markdown("---")
        
        # Service-specific metrics
        if "librarian" in selected_service.lower():
            # Librarian-specific data
            st.subheader("📈 Librarian Metrics")
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric("Total Assets Processed", f"{get_total_assets():,}")
            
            with metric_col2:
                st.metric("Processed Last Hour", f"{get_assets_last_hour():,}")
            
            with metric_col3:
                queue_length = get_librarian_queue_length()
                if queue_length is not None:
                    st.metric("Queue Length", f"{queue_length:,}")
                else:
                    st.metric("Queue Length", "N/A")
                    st.caption("Not available")
            
            with metric_col4:
                remaining = get_remaining_files()
                if remaining is not None:
                    st.metric("Files in Inbox", f"{remaining:,}")
                else:
                    st.metric("Files in Inbox", "N/A")
                    st.caption("Not available")
            
            st.markdown("---")
            
            # Latest Processed Files by Librarian
            st.subheader("📁 Latest Processed Files")
            recent_assets = get_recent_assets(limit=20)
            
            if recent_assets:
                try:
                    import pandas as pd
                except ImportError:
                    st.error("pandas not available")
                    return
                
                data = []
                for asset in recent_assets:
                    data.append({
                        "File": asset.get("original_name", "Unknown"),
                        "Size": f"{asset.get('size_bytes', 0) / 1024 / 1024:.2f} MB",
                        "Captured": asset.get("captured_at").strftime("%Y-%m-%d %H:%M") if asset.get("captured_at") else "N/A",
                        "Ingested": asset.get("ingested_at").strftime("%Y-%m-%d %H:%M:%S") if asset.get("ingested_at") else "N/A",
                        "Path": asset.get("final_path", "N/A")[:50] + "..." if len(asset.get("final_path", "")) > 50 else asset.get("final_path", "N/A"),
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No files processed yet")
        
        st.markdown("---")
        
        # Service Logs
        st.subheader(f"📋 {service_display_name} Logs")
        if DOCKER_AVAILABLE:
            logs = get_service_logs(selected_service, tail=200)
            if logs:
                log_lines = logs.strip().split('\n')
                recent_logs = '\n'.join(log_lines[-100:])  # Show last 100 lines
                st.code(recent_logs, language=None)
            else:
                st.info(f"No logs available for {selected_service}")
        else:
            st.warning("Docker unavailable - cannot fetch logs")


if __name__ == "__main__":
    main()

