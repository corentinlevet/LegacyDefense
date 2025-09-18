#!/usr/bin/env python3
"""
End-to-End Tests for GeneWeb-Python Web Application
Tests the complete user interface and functionality end-to-end.
"""

import pytest
import asyncio
import subprocess
import time
import signal
import os
from playwright.async_api import async_playwright, Page, Browser
from typing import Optional


class WebAppManager:
    """Manages the web application process for testing."""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.base_url = "http://localhost:8000"
    
    def start_server(self):
        """Start the web application server."""
        try:
            # Start the server in background
            self.process = subprocess.Popen(
                [r"C:/Users/noahc/Desktop/geneweb/.venv/Scripts/python.exe", "run_app.py"],
                cwd=r"c:\Users\noahc\Desktop\geneweb\geneweb-python\code",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Wait for server to start
            for attempt in range(30):  # Wait up to 30 seconds
                try:
                    import requests
                    response = requests.get(f"{self.base_url}/", timeout=2)
                    if response.status_code == 200:
                        print(f"Server started successfully on {self.base_url}")
                        return True
                except:
                    time.sleep(1)
                    continue
            
            print("Server failed to start within timeout")
            return False
            
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the web application server."""
        if self.process:
            try:
                # Send CTRL+BREAK to the process group
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                pass
            self.process = None


@pytest.fixture(scope="session")
def web_app():
    """Fixture to manage web application lifecycle."""
    manager = WebAppManager()
    
    # Ensure test data exists
    print("Setting up test data...")
    result = subprocess.run([
        r"C:/Users/noahc/Desktop/geneweb/.venv/Scripts/python.exe", 
        "test_data_generator_fixed.py"
    ], cwd=r"c:\Users\noahc\Desktop\geneweb\geneweb-python\code", capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Test data setup failed: {result.stderr}")
        pytest.skip("Could not set up test data")
    
    # Start server
    print("Starting web application server...")
    if not manager.start_server():
        pytest.skip("Could not start web application server")
    
    yield manager
    
    # Cleanup
    print("Stopping web application server...")
    manager.stop_server()


@pytest.fixture
async def browser():
    """Fixture to provide browser instance."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser: Browser):
    """Fixture to provide page instance."""
    page = await browser.new_page()
    yield page
    await page.close()


class TestHomePageE2E:
    """End-to-end tests for the home page."""
    
    async def test_home_page_loads(self, web_app: WebAppManager, page: Page):
        """Test that the home page loads successfully."""
        await page.goto(web_app.base_url)
        
        # Check page title
        title = await page.title()
        assert "GeneWeb" in title
        
        # Check main heading exists
        heading = page.locator("h1")
        await heading.wait_for()
        assert await heading.is_visible()
        
        # Check navigation menu
        nav = page.locator("nav")
        assert await nav.is_visible()
    
    async def test_home_page_navigation_links(self, web_app: WebAppManager, page: Page):
        """Test that navigation links work correctly."""
        await page.goto(web_app.base_url)
        
        # Test "All Persons" link
        persons_link = page.locator('a[href="/persons"]')
        await persons_link.wait_for()
        assert await persons_link.is_visible()
        
        # Click and verify navigation
        await persons_link.click()
        await page.wait_for_url("**/persons")
        
        # Check we're on the persons page
        persons_heading = page.locator("h2:has-text('All Persons')")
        await persons_heading.wait_for()
        assert await persons_heading.is_visible()
    
    async def test_home_page_statistics(self, web_app: WebAppManager, page: Page):
        """Test that statistics are displayed on home page."""
        await page.goto(web_app.base_url)
        
        # Look for statistics section
        stats_section = page.locator(".statistics, .stats, [class*='stat']")
        if await stats_section.count() > 0:
            assert await stats_section.first.is_visible()
            
            # Check for person count
            person_count = page.locator(":has-text('persons'), :has-text('Persons'), :has-text('individuals')")
            if await person_count.count() > 0:
                assert await person_count.first.is_visible()


class TestPersonsPageE2E:
    """End-to-end tests for the persons listing page."""
    
    async def test_persons_page_loads(self, web_app: WebAppManager, page: Page):
        """Test that the persons page loads and displays person data."""
        await page.goto(f"{web_app.base_url}/persons")
        
        # Check page loads
        heading = page.locator("h2:has-text('All Persons'), h1:has-text('Persons')")
        await heading.wait_for(timeout=10000)
        assert await heading.is_visible()
        
        # Check that persons are displayed
        person_cards = page.locator(".person-card, .person, [class*='person']")
        await page.wait_for_timeout(2000)  # Wait for data to load
        
        person_count = await person_cards.count()
        assert person_count > 0, "No persons displayed on the page"
        print(f"Found {person_count} person cards")
    
    async def test_persons_display_names(self, web_app: WebAppManager, page: Page):
        """Test that person names are displayed correctly."""
        await page.goto(f"{web_app.base_url}/persons")
        
        # Wait for content to load
        await page.wait_for_timeout(3000)
        
        # Look for specific test names we know should exist
        test_names = ["John Smith", "Mary Johnson", "Robert Smith", "Elizabeth Brown"]
        
        found_names = []
        for name in test_names:
            name_element = page.locator(f":has-text('{name}')")
            if await name_element.count() > 0:
                found_names.append(name)
        
        assert len(found_names) > 0, f"No test names found. Expected at least one of: {test_names}"
        print(f"Found test names: {found_names}")
    
    async def test_person_links_functional(self, web_app: WebAppManager, page: Page):
        """Test that clicking on a person navigates to their detail page."""
        await page.goto(f"{web_app.base_url}/persons")
        
        # Wait for content
        await page.wait_for_timeout(3000)
        
        # Find first person link
        person_links = page.locator("a[href*='/person/'], a[href*='/persons/']")
        
        if await person_links.count() > 0:
            first_link = person_links.first
            href = await first_link.get_attribute("href")
            
            # Click the link
            await first_link.click()
            
            # Check we navigated to person detail page
            await page.wait_for_url("**/person/**")
            
            # Verify person detail page content
            detail_content = page.locator("h1, h2, .person-detail, [class*='detail']")
            await detail_content.wait_for(timeout=5000)
            assert await detail_content.is_visible()


class TestPersonDetailPageE2E:
    """End-to-end tests for individual person detail pages."""
    
    async def test_person_detail_page_loads(self, web_app: WebAppManager, page: Page):
        """Test that a person detail page loads correctly."""
        # Navigate via persons page to get a valid person ID
        await page.goto(f"{web_app.base_url}/persons")
        await page.wait_for_timeout(3000)
        
        # Find and click first person link
        person_links = page.locator("a[href*='/person/']")
        
        if await person_links.count() > 0:
            await person_links.first.click()
            
            # Wait for person detail page
            await page.wait_for_url("**/person/**")
            
            # Check for person details
            person_info = page.locator(".person-info, .person-detail, h1, h2")
            await person_info.wait_for()
            assert await person_info.is_visible()
    
    async def test_person_detail_contains_genealogical_data(self, web_app: WebAppManager, page: Page):
        """Test that person detail shows genealogical information."""
        await page.goto(f"{web_app.base_url}/persons")
        await page.wait_for_timeout(3000)
        
        # Navigate to first person
        person_links = page.locator("a[href*='/person/']")
        if await person_links.count() > 0:
            await person_links.first.click()
            await page.wait_for_url("**/person/**")
            
            # Look for genealogical data elements
            genealogy_elements = [
                ":has-text('Birth')",
                ":has-text('Death')", 
                ":has-text('Father')",
                ":has-text('Mother')",
                ":has-text('Family')",
                ":has-text('Parents')",
            ]
            
            found_elements = []
            for element in genealogy_elements:
                if await page.locator(element).count() > 0:
                    found_elements.append(element)
            
            # Should find at least some genealogical information
            assert len(found_elements) > 0, "No genealogical information found on person detail page"
            print(f"Found genealogical elements: {found_elements}")


class TestResponsiveDesignE2E:
    """End-to-end tests for responsive design."""
    
    async def test_mobile_responsive(self, web_app: WebAppManager, page: Page):
        """Test that the site works on mobile viewport."""
        # Set mobile viewport
        await page.set_viewport_size({"width": 375, "height": 667})
        
        await page.goto(web_app.base_url)
        
        # Check navigation is accessible
        nav = page.locator("nav")
        assert await nav.is_visible()
        
        # Check content doesn't overflow
        body = page.locator("body")
        body_width = await body.bounding_box()
        assert body_width["width"] <= 375, "Content overflows mobile viewport"
    
    async def test_tablet_responsive(self, web_app: WebAppManager, page: Page):
        """Test that the site works on tablet viewport."""
        # Set tablet viewport
        await page.set_viewport_size({"width": 768, "height": 1024})
        
        await page.goto(web_app.base_url)
        
        # Navigation should still be visible
        nav = page.locator("nav")
        assert await nav.is_visible()
        
        # Test persons page on tablet
        await page.goto(f"{web_app.base_url}/persons")
        await page.wait_for_timeout(2000)
        
        person_cards = page.locator(".person-card, .person, [class*='person']")
        if await person_cards.count() > 0:
            assert await person_cards.first.is_visible()


class TestSearchFunctionalityE2E:
    """End-to-end tests for search functionality."""
    
    async def test_search_exists(self, web_app: WebAppManager, page: Page):
        """Test that search functionality exists."""
        await page.goto(web_app.base_url)
        
        # Look for search form or input
        search_elements = page.locator(
            "input[type='search'], input[name*='search'], input[placeholder*='search'], "
            "input[placeholder*='Search'], form[class*='search'], .search"
        )
        
        if await search_elements.count() > 0:
            search_input = search_elements.first
            assert await search_input.is_visible()
            
            # Try to use search
            await search_input.fill("Smith")
            
            # Look for search button or form submission
            search_button = page.locator(
                "button[type='submit'], input[type='submit'], button:has-text('Search')"
            )
            
            if await search_button.count() > 0:
                await search_button.click()
                await page.wait_for_timeout(2000)
        else:
            pytest.skip("No search functionality found")


if __name__ == "__main__":
    # Install required packages
    subprocess.run([
        r"C:/Users/noahc/Desktop/geneweb/.venv/Scripts/python.exe", "-m", "pip", 
        "install", "requests"
    ])
    
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])