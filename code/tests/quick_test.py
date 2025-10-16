#!/usr/bin/env python3
"""
Quick Sanity Check for GeneWeb-Python Web Application
Fast verification that the application is working correctly.
"""

import subprocess
import time
import signal
import requests
import sys
from typing import Optional


class QuickTest:
    """Quick sanity test for the web application."""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.base_url = "http://localhost:8000"
        self.timeout = 30  # Maximum 30 seconds total
    
    def start_server(self):
        """Start the web application server quickly."""
        print("🚀 Starting GeneWeb server...")
        try:
            self.process = subprocess.Popen(
                [r"C:/Users/noahc/Desktop/geneweb/.venv/Scripts/python.exe", "run_app.py"],
                cwd=r"c:\Users\noahc\Desktop\geneweb\geneweb-python\code",
                stdout=subprocess.DEVNULL,  # Suppress output
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Quick startup check - only wait 10 seconds
            start_time = time.time()
            for attempt in range(10):
                if time.time() - start_time > 10:
                    print("❌ Server startup timeout (10s)")
                    return False
                    
                try:
                    response = requests.get(f"{self.base_url}/", timeout=2)
                    if response.status_code == 200:
                        print(f"✅ Server started in {time.time() - start_time:.1f}s")
                        return True
                except:
                    time.sleep(1)
            
            print("❌ Server failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Server start error: {e}")
            return False
    
    def stop_server(self):
        """Stop the server quickly."""
        if self.process:
            try:
                print("🛑 Stopping server...")
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
                
                # Quick shutdown - only wait 3 seconds
                try:
                    self.process.wait(timeout=3)
                    print("✅ Server stopped")
                except subprocess.TimeoutExpired:
                    print("⚠ Force stopping...")
                    self.process.terminate()
                    self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                    self.process.wait()
                except:
                    pass
            finally:
                self.process = None
    
    def run_quick_tests(self):
        """Run quick functionality tests."""
        tests_passed = 0
        total_tests = 5
        
        print("\n📋 Running quick functionality tests...")
        
        # Test 1: Home page
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200 and ("geneweb" in response.text.lower() or "GeneWeb" in response.text):
                print("✅ Test 1/5: Home page loads")
                tests_passed += 1
            else:
                print("❌ Test 1/5: Home page failed")
        except Exception as e:
            print(f"❌ Test 1/5: Home page error - {e}")
        
        # Test 2: Persons page
        try:
            response = requests.get(f"{self.base_url}/persons", timeout=5)
            if response.status_code == 200:
                print("✅ Test 2/5: Persons page loads")
                tests_passed += 1
            else:
                print("❌ Test 2/5: Persons page failed")
        except Exception as e:
            print(f"❌ Test 2/5: Persons page error - {e}")
        
        # Test 3: Person detail
        try:
            response = requests.get(f"{self.base_url}/person/1", timeout=5)
            if response.status_code in [200, 404]:  # Either works or proper 404
                print("✅ Test 3/5: Person detail handled")
                tests_passed += 1
            else:
                print("❌ Test 3/5: Person detail failed")
        except Exception as e:
            print(f"❌ Test 3/5: Person detail error - {e}")
        
        # Test 4: 404 handling
        try:
            response = requests.get(f"{self.base_url}/nonexistent", timeout=5)
            if response.status_code == 404:
                print("✅ Test 4/5: 404 error handling")
                tests_passed += 1
            else:
                print("❌ Test 4/5: 404 handling failed")
        except Exception as e:
            print(f"❌ Test 4/5: 404 handling error - {e}")
        
        # Test 5: Database connectivity
        try:
            from core.database import DatabaseManager, PersonORM
            db = DatabaseManager()
            session = db.get_session()
            count = session.query(PersonORM).count()
            session.close()
            
            if count > 0:
                print(f"✅ Test 5/5: Database has {count} persons")
                tests_passed += 1
            else:
                print("❌ Test 5/5: Database empty")
        except Exception as e:
            print(f"❌ Test 5/5: Database error - {e}")
        
        return tests_passed, total_tests
    
    def run_all(self):
        """Run complete quick test suite."""
        start_time = time.time()
        
        print("🧪 GeneWeb-Python Quick Sanity Check")
        print("=" * 40)
        
        # Check timeout
        if time.time() - start_time > self.timeout:
            print(f"❌ Total timeout exceeded ({self.timeout}s)")
            return False
        
        # Start server
        if not self.start_server():
            return False
        
        try:
            # Check timeout before tests
            if time.time() - start_time > self.timeout - 10:
                print(f"❌ Not enough time for tests (timeout: {self.timeout}s)")
                return False
            
            # Run tests
            passed, total = self.run_quick_tests()
            
            elapsed = time.time() - start_time
            print(f"\n📊 Results: {passed}/{total} tests passed in {elapsed:.1f}s")
            
            if passed == total:
                print("🎉 All tests passed! Application is working correctly.")
                return True
            elif passed >= total * 0.8:  # 80% pass rate
                print("⚠ Most tests passed. Application mostly functional.")
                return True
            else:
                print("❌ Many tests failed. Application has issues.")
                return False
                
        finally:
            self.stop_server()


def main():
    """Main entry point."""
    tester = QuickTest()
    
    try:
        success = tester.run_all()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
        tester.stop_server()
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        tester.stop_server()
        sys.exit(3)


if __name__ == "__main__":
    main()