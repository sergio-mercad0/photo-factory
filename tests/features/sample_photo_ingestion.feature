# =============================================================================
# SAMPLE FEATURE FILE TEMPLATE
# =============================================================================
# This is a template demonstrating pytest-bdd feature file conventions
# for the Photo Factory project. Copy and modify for new features.
#
# Test Markers (use in conftest.py step definitions):
#   @pytest.mark.unit        - Build-time safe (mocked, no I/O)
#   @pytest.mark.integration - Runtime only (requires DB/services)
#   @pytest.mark.browser     - Runtime only (uses browser tools)
#   @pytest.mark.real_asset  - Runtime only (uses actual photos/videos)
#   @pytest.mark.slow        - Decoupled from build (media processing)
#   @pytest.mark.heavy       - Decoupled from build (GPU, ML inference)
# =============================================================================

@unit
Feature: Photo Ingestion Pipeline
    As a Photo Factory user
    I want photos dropped in the inbox to be automatically organized
    So that I don't have to manually sort my photos by date

    Background:
        Given the Photo Factory system is initialized
        And the inbox directory exists
        And the storage directory exists

    # -------------------------------------------------------------------------
    # HAPPY PATH SCENARIOS (Unit Tests - Build Time)
    # -------------------------------------------------------------------------
    @unit
    Scenario: Photo is organized by capture date
        Given a photo "vacation.jpg" exists in the inbox
        And the photo has capture date "2025-06-15"
        When the librarian processes the inbox
        Then the photo should be moved to "Storage/Originals/2025/2025-06-15/vacation.jpg"
        And the photo should be recorded in the database
        And the original file should be removed from the inbox

    @unit
    Scenario: Duplicate photo is detected and removed
        Given a photo "sunset.jpg" with hash "abc123" exists in the inbox
        And a photo with hash "abc123" already exists in storage
        When the librarian processes the inbox
        Then the inbox photo should be deleted
        And the database should record a duplicate detection
        And no new file should be added to storage

    @unit
    Scenario: Photo with same name but different content is renamed
        Given a photo "IMG_001.jpg" with hash "hash1" exists in the inbox
        And a different photo "IMG_001.jpg" with hash "hash2" exists in storage dated "2025-06-15"
        When the librarian processes the inbox
        Then a file "IMG_001_copy_1.jpg" should exist in "Storage/Originals/2025/2025-06-15/"
        And the original storage file should be unchanged

    # -------------------------------------------------------------------------
    # INTEGRATION SCENARIOS (Runtime Tests)
    # -------------------------------------------------------------------------
    @integration
    Scenario: End-to-end photo processing with real database
        Given the PostgreSQL database is running
        And the librarian service is started
        And a test photo is placed in the inbox
        When I wait for the librarian to process
        Then the photo should appear in the correct date folder
        And the database should contain the photo metadata
        And the heartbeat should show "OK" status

    # -------------------------------------------------------------------------
    # HEAVY TESTS (Media Processing - Decoupled from Build)
    # -------------------------------------------------------------------------
    @slow @real_asset
    Scenario: Large photo batch is processed correctly
        Given 100 photos exist in the inbox with various dates
        When the librarian processes all photos
        Then each photo should be in its correct date folder
        And no duplicates should exist in storage
        And processing should complete within 60 seconds

    @slow @real_asset
    Scenario: Video file metadata is extracted correctly
        Given a video file "family_video.mp4" exists in the inbox
        And the video has creation date "2024-12-25"
        When the librarian processes the inbox
        Then the video should be moved to "Storage/Originals/2024/2024-12-25/"
        And the database should record the video metadata including duration


# =============================================================================
# STEP DEFINITION TEMPLATE (for conftest.py)
# =============================================================================
# Add these step definitions to tests/conftest.py or the service conftest.py:
#
# from pytest_bdd import given, when, then, parsers, scenarios
#
# # Load all scenarios from this feature file
# scenarios('features/sample_photo_ingestion.feature')
#
# @given("the Photo Factory system is initialized")
# def system_initialized(bdd_context):
#     bdd_context["initialized"] = True
#
# @given("the inbox directory exists")
# def inbox_exists(tmp_inbox, bdd_context):
#     assert tmp_inbox.exists()
#     bdd_context["inbox"] = tmp_inbox
#
# @given(parsers.parse('a photo "{filename}" exists in the inbox'))
# def photo_in_inbox(bdd_context, create_test_image, filename):
#     photo = create_test_image(bdd_context["inbox"], filename)
#     bdd_context["photo"] = photo
#
# @when("the librarian processes the inbox")
# def librarian_processes(bdd_context, librarian_service):
#     result = librarian_service.process_inbox()
#     bdd_context["result"] = result
#
# @then(parsers.parse('the photo should be moved to "{expected_path}"'))
# def photo_moved(bdd_context, tmp_storage, expected_path):
#     # Verify the photo was moved to the expected location
#     assert (tmp_storage.parent.parent / expected_path).exists()
# =============================================================================






