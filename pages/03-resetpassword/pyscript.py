import js
from pyscript import window, document
from pyodide.ffi import create_proxy
from pyodide.http import pyfetch
from abc import ABC, abstractmethod

class AbstractWidget(ABC):
    def __init__(self, element_id):
        self.element_id = element_id
        self._element = None
    
    @property
    def element(self):
        if not self._element:
            self._element = document.querySelector(f"#{self.element_id}")
        return self._element
    
    @abstractmethod
    def initializeWidget(self):
        pass
    
class SignInWidget(AbstractWidget):
    def __init__(self, element_id):
        super().__init__(element_id)

    def initializeWidget(self):
        self.reset_element = document.querySelector("#reset__btn")
        self.reset_element.onclick = self.resetPassword
        self.hidden_element = document.querySelector(".background__black--faded")
        
        if not self.hidden_element:
            print("Error: Could not find element with class 'background__black--faded'")
            return

    async def submitForm(self, event):
        event.preventDefault()
        username = document.querySelector("#username").value
        password = document.querySelector("#password").value
        try:
            response = await pyfetch(
                url=f"/user/signIn/?key={username}&password={password}", 
                method='POST', 
                headers={'Content-Type': 'application/json'}
            )
            if response.ok:
                data = await response.json()
                if 'detail' in data:
                    self.hidden_element.classList.remove("hidden")
                else:
                    window.location.href = "/"
        except Exception as e:
            print(e)
    
    async def resetPassword(self, event):
        event.preventDefault()
        email = document.querySelector("#email").value
        try:
            response = await pyfetch(
                url=f"/user/resetPassword/?email={email}", 
                method='POST', 
                headers={'Content-Type': 'application/json'}
            )
            if response.ok:
                data = await response.json()
                if 'detail' in data:
                    window.location.href = "/signIn"
                else:
                    window.location.href = "/signIn"
        except Exception as e:
            print(e)

if __name__ == "__main__":
    w = SignInWidget("signin__form")
    w.initializeWidget()