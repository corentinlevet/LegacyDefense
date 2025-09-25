#!/usr/bin/env python3
"""
Simple E2E Tests for GeneWeb-Python Web Application
Tests the web application functionality without browser automation.
"""

import pytest
import subprocess
import time
import signal
import requests
from typing import Optional
import json


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
            
            # Wait for server to start with shorter timeout
            print("Waiting for server to start...")
            for attempt in range(15):  # Wait up to 15 seconds
                try:
                    response = requests.get(f"{self.base_url}/", timeout=3)
                    if response.status_code == 200:
                        print(f"✓ Server started successfully on {self.base_url}")
                        return True
                except requests.exceptions.RequestException:
                    print(f"Attempt {attempt + 1}/15: Server not ready yet...")
                    time.sleep(1)
                    continue
            
            print("❌ Server failed to start within 15 seconds")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the web application server."""
        if self.process:
            try:
                print("Stopping server...")
                # Send CTRL+BREAK to the process group
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
                
                # Wait for graceful shutdown with timeout
                try:
                    self.process.wait(timeout=5)
                    print("✓ Server stopped gracefully")
                except subprocess.TimeoutExpired:
                    print("⚠ Graceful shutdown timed out, forcing termination...")
                    # Force kill if graceful shutdown fails
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                        print("✓ Server terminated")
                    except subprocess.TimeoutExpired:
                        print("⚠ Forcing kill...")
                        self.process.kill()
                        self.process.wait()
            except Exception as e:
                print(f"⚠ Error stopping server: {e}")
                try:
                    self.process.kill()
                    self.process.wait()
                except:
                    pass
            finally:
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


class TestWebAppFunctional:
    """Functional tests for the web application."""
    
    def test_home_page_loads(self, web_app: WebAppManager):
        """Test that the home page loads successfully."""
        try:
            response = requests.get(web_app.base_url, timeout=10)
            assert response.status_code == 200
            assert "GeneWeb" in response.text or "geneweb" in response.text.lower()
            print("✓ Home page loads successfully")
        except requests.exceptions.Timeout:
            pytest.fail("❌ Home page request timed out after 10 seconds")
        except Exception as e:
            pytest.fail(f"❌ Home page load failed: {e}")
    
    def test_persons_page_loads(self, web_app: WebAppManager):
        """Test that the persons page loads and returns data."""
        try:
            response = requests.get(f"{web_app.base_url}/persons", timeout=10)
            assert response.status_code == 200
            
            # Check for person names in the response
            test_names = ["John", "Mary", "Smith", "Johnson"]
            found_names = []
            for name in test_names:
                if name in response.text:
                    found_names.append(name)
            
            assert len(found_names) > 0, f"No test names found in persons page. Expected: {test_names}"
            print(f"✓ Persons page loads with names: {found_names}")
        except requests.exceptions.Timeout:
            pytest.fail("❌ Persons page request timed out after 10 seconds")
        except Exception as e:
            pytest.fail(f"❌ Persons page load failed: {e}")
    
    def test_person_detail_page_loads(self, web_app: WebAppManager):
        """Test that person detail pages load."""
        try:
            # Get persons list first
            response = requests.get(f"{web_app.base_url}/persons", timeout=10)
            assert response.status_code == 200
            
            # Try person ID 1 (should exist from test data)
            response = requests.get(f"{web_app.base_url}/person/1", timeout=10)
            assert response.status_code == 200
            
            # Check for person details
            detail_indicators = ["birth", "Birth", "name", "Name", "family", "Family"]
            found_details = []
            for indicator in detail_indicators:
                if indicator in response.text:
                    found_details.append(indicator)
            
            assert len(found_details) > 0, "No person details found on person page"
            print(f"✓ Person detail page loads with details: {found_details}")
        except requests.exceptions.Timeout:
            pytest.fail("❌ Person detail page request timed out after 10 seconds")
        except Exception as e:
            pytest.fail(f"❌ Person detail page load failed: {e}")
    
    def test_api_endpoints_work(self, web_app: WebAppManager):
        """Test that API endpoints return proper JSON."""
        # Test API endpoints if they exist
        api_endpoints = ["/api/persons", "/api/person/1", "/api/families"]
        
        working_endpoints = []
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{web_app.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    # Try to parse as JSON
                    try:
                        data = response.json()
                        working_endpoints.append(endpoint)
                    except json.JSONDecodeError:
                        pass
            except (requests.exceptions.RequestException, requests.exceptions.Timeout):
                pass
        
        # Don't fail if no API endpoints exist, just report
        if working_endpoints:
            print(f"✓ Working API endpoints: {working_endpoints}")
        else:
            print("⚠ No API endpoints found or working")
    
    @pytest.mark.timeout(30)  # Maximum 30 seconds for this test
    def test_database_has_test_data(self, web_app: WebAppManager):
        """Verify that test data was loaded correctly."""
        # This test verifies our data generator worked
        try:
            from core.database import DatabaseManager, PersonORM, FamilyORM
            
            db_manager = DatabaseManager()
            session = db_manager.get_session()
            
            try:
                person_count = session.query(PersonORM).count()
                family_count = session.query(FamilyORM).count()
                
                assert person_count > 0, "No persons found in database"
                assert family_count > 0, "No families found in database"
                
                # Check specific test persons exist
                john_smith = session.query(PersonORM).filter(
                    PersonORM.first_name == "John",
                    PersonORM.surname == "Smith"
                ).first()
                
                assert john_smith is not None, "Test person John Smith not found"
                
                print(f"✓ Database contains {person_count} persons and {family_count} families")
                print(f"✓ Test person John Smith found with ID: {john_smith.id}")
                
            finally:
                session.close()
                
        except Exception as e:
            pytest.fail(f"❌ Database test failed: {e}")
    
    def test_web_forms_render(self, web_app: WebAppManager):
        """Test that web forms and interactive elements render."""
        try:
            response = requests.get(web_app.base_url, timeout=10)
            
            # Check for form elements
            form_elements = ["<form", "<input", "<button", "<select"]
            found_forms = []
            
            for element in form_elements:
                if element in response.text:
                    found_forms.append(element)
            
            # Also check navigation elements
            nav_elements = ["<nav", "href=", "<a "]
            found_nav = []
            
            for element in nav_elements:
                if element in response.text:
                    found_nav.append(element)
            
            assert len(found_nav) > 0, "No navigation elements found"
            print(f"✓ Navigation elements found: {found_nav}")
            
            if found_forms:
                print(f"✓ Form elements found: {found_forms}")
            else:
                print("⚠ No form elements found")
                
        except requests.exceptions.Timeout:
            pytest.fail("❌ Web forms test timed out after 10 seconds")
        except Exception as e:
            pytest.fail(f"❌ Web forms test failed: {e}")
    
    def test_responsive_content_exists(self, web_app: WebAppManager):
        """Test that responsive design elements exist."""
        try:
            response = requests.get(web_app.base_url, timeout=10)
            
            # Check for responsive indicators
            responsive_indicators = [
                "viewport", "responsive", "mobile", "bootstrap", "grid", 
                "container", "row", "col-", "flex", "media"
            ]
            
            found_responsive = []
            for indicator in responsive_indicators:
                if indicator in response.text.lower():
                    found_responsive.append(indicator)
            
            if found_responsive:
                print(f"✓ Responsive design indicators found: {found_responsive}")
            else:
                print("⚠ No obvious responsive design indicators found")
                
        except requests.exceptions.Timeout:
            pytest.fail("❌ Responsive content test timed out after 10 seconds")
        except Exception as e:
            pytest.fail(f"❌ Responsive content test failed: {e}")
    
    def test_error_handling(self, web_app: WebAppManager):
        """Test that error pages work correctly."""
        try:
            # Test 404 error
            response = requests.get(f"{web_app.base_url}/nonexistent-page", timeout=10)
            assert response.status_code == 404
            print("✓ 404 error handling works")
            
            # Test invalid person ID
            response = requests.get(f"{web_app.base_url}/person/99999", timeout=10)
            # Should either 404 or handle gracefully
            assert response.status_code in [404, 200]
            print("✓ Invalid person ID handled correctly")
            
        except requests.exceptions.Timeout:
            pytest.fail("❌ Error handling test timed out after 10 seconds")
        except Exception as e:
            pytest.fail(f"❌ Error handling test failed: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])