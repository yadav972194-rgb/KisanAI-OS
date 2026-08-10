"""
KisanAI OS
API Response Module
Version: 1.0.0
"""


class APIResponse:

    def __init__(self, success=True, message="", data=None):
        self.success = success
        self.message = message
        self.data = data

    def to_dict(self):
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data
        }


if __name__ == "__main__":

    response = APIResponse(
        success=True,
        message="Farmer Data Retrieved Successfully",
        data={
            "name": "Pradeep Yadav",
            "mobile": "9876543210"
        }
    )

    print("=" * 50)
    print("API Response Loaded Successfully")
    print("=" * 50)
    print(response.to_dict())