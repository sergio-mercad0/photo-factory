# =============================================================================
# RESOURCE MONITORING FEATURE
# =============================================================================
# Epic 6: Enhanced Dashboard
# Workstream 6.0: Flicker-Free Resource Monitoring
#
# This feature file defines behavior specifications for the dashboard's
# system resource monitoring capabilities (CPU, RAM, Disk metrics).
#
# Test Markers:
#   @unit        - Build-time safe (mocked, no I/O)
#   @integration - Runtime only (requires services running)
#   @browser     - Runtime only (uses browser tools for visual verification)
# =============================================================================

@unit
Feature: Dashboard Resource Monitoring
    As a Photo Factory operator
    I want to see CPU, RAM, and Disk usage in the dashboard header
    So that I can monitor system health at a glance

    Background:
        Given the dashboard module is loaded
        And psutil is available for system metrics

    # -------------------------------------------------------------------------
    # RESOURCE COLLECTION SCENARIOS (Unit Tests - Build Time)
    # -------------------------------------------------------------------------
    @unit
    Scenario: CPU percentage is collected from the system
        Given the system CPU usage is 45 percent
        When I request system resources
        Then the result should contain cpu_percent with value 45

    @unit
    Scenario: RAM metrics are collected with used and total GB
        Given the system has 16 GB total RAM
        And 10 GB of RAM is currently used
        When I request system resources
        Then the result should contain ram_used_gb approximately 10
        And the result should contain ram_total_gb approximately 16
        And the result should contain ram_percent approximately 62.5

    @unit
    Scenario: Disk metrics are collected with used and total GB
        Given the system has 500 GB total disk space
        And 350 GB of disk space is used
        When I request system resources
        Then the result should contain disk_used_gb approximately 350
        And the result should contain disk_total_gb approximately 500
        And the result should contain disk_percent approximately 70

    @unit
    Scenario: All resource keys are present in response
        Given the system has normal resource values
        When I request system resources
        Then the result should contain all required keys:
            | key            |
            | cpu_percent    |
            | ram_percent    |
            | ram_used_gb    |
            | ram_total_gb   |
            | disk_percent   |
            | disk_used_gb   |
            | disk_total_gb  |

    @unit
    Scenario: Graceful handling when psutil fails
        Given psutil raises an exception on CPU query
        When I request system resources
        Then all resource values should be zero
        And no exception should be raised

    # -------------------------------------------------------------------------
    # HEADER RENDERING SCENARIOS (Unit Tests - Build Time)
    # -------------------------------------------------------------------------
    @unit
    Scenario: Resource metrics are displayed in header row
        Given the dashboard is rendering
        And system resources show 50% CPU, 60% RAM, 70% Disk
        When I render the resource header
        Then I should see a CPU metric with value "50%"
        And I should see a RAM metric with value "60%"
        And I should see a Disk metric with value "70%"

    @unit
    Scenario: Header uses four-column layout
        Given the dashboard is rendering
        When I render the resource header
        Then the layout should have four columns
        And the columns should have ratio 1:1.5:1.5:3

    @unit
    Scenario: RAM metric shows used/total GB in delta
        Given the dashboard is rendering
        And RAM usage is 8.5 GB of 16 GB total
        When I render the resource header
        Then the RAM metric delta should contain "8.5/16.0 GB"

    @unit
    Scenario: Disk metric shows used/total GB in delta
        Given the dashboard is rendering
        And Disk usage is 350 GB of 500 GB total
        When I render the resource header
        Then the Disk metric delta should contain "350/500 GB"

    @unit
    Scenario: Service selector is included in header
        Given the dashboard is rendering
        And available services are "librarian" and "dashboard"
        When I render the resource header
        Then I should see a service selector
        And the selector should have "All Services" as first option
        And the selector should include "librarian"
        And the selector should include "dashboard"

    @unit
    Scenario: Service selector returns selected value
        Given the dashboard is rendering
        And the user selects "librarian" service
        When I render the resource header
        Then the header should return "librarian"

    @unit
    Scenario: Header handles no available services
        Given the dashboard is rendering
        And no services are available
        When I render the resource header
        Then I should see a warning about no services
        And the header should return "All Services"

    # -------------------------------------------------------------------------
    # FORMAT VALIDATION SCENARIOS (Unit Tests - Build Time)
    # -------------------------------------------------------------------------
    @unit
    Scenario: CPU percentage is formatted without decimals
        Given the CPU usage is 45.789 percent
        When I format the CPU for display
        Then the displayed value should be "46%"

    @unit
    Scenario: RAM GB values are formatted with one decimal
        Given RAM usage is 10.123 GB of 16.789 GB total
        When I format the RAM for display
        Then the delta should show "10.1/16.8 GB"

    @unit
    Scenario: Disk GB values are formatted without decimals
        Given Disk usage is 375.789 GB of 500.123 GB total
        When I format the Disk for display
        Then the delta should show "376/500 GB"

    # -------------------------------------------------------------------------
    # EDGE CASE SCENARIOS (Unit Tests - Build Time)
    # -------------------------------------------------------------------------
    @unit
    Scenario: Handle very small memory systems
        Given the system has 512 MB total RAM
        And 460 MB of RAM is used
        When I request system resources
        Then ram_total_gb should be approximately 0.5
        And ram_used_gb should be approximately 0.45

    @unit
    Scenario: Handle very large disk systems
        Given the system has 10 TB total disk space
        And 4 TB is used
        When I request system resources
        Then disk_total_gb should be approximately 10000
        And disk_used_gb should be approximately 4000

    @unit
    Scenario: Handle high resource usage
        Given CPU usage is 99.9 percent
        And RAM usage is 95.5 percent
        And Disk usage is 98 percent
        When I request system resources
        Then cpu_percent should be 99.9
        And ram_percent should be 95.5
        And disk_percent should be 98

    @unit
    Scenario: Handle zero resource usage
        Given CPU usage is 0 percent
        And RAM usage is 0 percent
        And Disk usage is 0 percent
        When I request system resources
        Then all percentage values should be zero

    # -------------------------------------------------------------------------
    # REFRESH BEHAVIOR SCENARIOS (Unit Tests - Build Time)
    # -------------------------------------------------------------------------
    @unit
    Scenario: Resource metrics update without page flicker
        Given the dashboard is running with auto-refresh enabled
        And CSS transitions are applied to metric elements
        When the refresh interval triggers
        Then the resource metrics should update in-place
        And no visual flicker should occur due to CSS transitions

    @unit
    Scenario: Resource function uses caching appropriately
        Given the get_system_resources function has a 2-second TTL cache
        When I call get_system_resources twice within 1 second
        Then the underlying psutil should only be called once

    # -------------------------------------------------------------------------
    # INTEGRATION SCENARIOS (Runtime Tests - Require Services)
    # -------------------------------------------------------------------------
    @integration
    Scenario: Dashboard displays real system resources
        Given the dashboard service is running
        When I view the dashboard header
        Then I should see real CPU percentage
        And I should see real RAM usage
        And I should see real Disk usage

    @integration @browser
    Scenario: Resource header is visually correct in browser
        Given I navigate to the dashboard URL
        When the page loads completely
        Then I should see the CPU metric in the header
        And I should see the RAM metric with GB values
        And I should see the Disk metric with GB values
        And I should see the service selector dropdown

    @integration @browser
    Scenario: Resource metrics update smoothly on refresh
        Given I am viewing the dashboard in the browser
        And auto-refresh is enabled at 10 second intervals
        When the auto-refresh occurs
        Then the resource values should update
        And the page should not show visible flickering
        And the layout should remain stable


# =============================================================================
# STEP DEFINITION NOTES
# =============================================================================
# Step definitions for these scenarios should be added to:
#   Src/Dashboard/tests/conftest.py
#
# Example step definitions:
#
# from pytest_bdd import given, when, then, parsers, scenarios
# from unittest.mock import MagicMock, patch
#
# scenarios('features/resource_monitoring.feature')
#
# @given(parsers.parse('the system CPU usage is {cpu:d} percent'))
# def system_cpu_usage(bdd_context, cpu):
#     bdd_context['mock_cpu'] = float(cpu)
#
# @when('I request system resources')
# def request_system_resources(bdd_context):
#     with patch('Src.Dashboard.dashboard.psutil') as mock_psutil:
#         mock_psutil.cpu_percent.return_value = bdd_context.get('mock_cpu', 50.0)
#         # ... setup other mocks ...
#         from Src.Dashboard.dashboard import get_system_resources
#         bdd_context['result'] = get_system_resources()
#
# @then(parsers.parse('the result should contain cpu_percent with value {expected:d}'))
# def verify_cpu_percent(bdd_context, expected):
#     assert bdd_context['result']['cpu_percent'] == float(expected)
# =============================================================================
