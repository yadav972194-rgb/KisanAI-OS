"""
KisanAI OS
API Request
Version: 1.0.0
"""


class APIRequest:

    def __init__(self, endpoint, method="GET", data=None):
        self.endpoint = endpoint
        self.method = method
        self.data = data if data else {}

    def to_dict(self):
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "data": self.data
        }


if __name__ == "__main__":

    request = APIRequest(
        endpoint="/api/farmer",
        method="POST",
        data={
            "name": "Pradeep Yadav",
            "mobile": "9876543210"
        }
    )

    print("=" * 50)
    print("API Request Loaded Successfully")
    print("=" * 50)
    print(request.to_dict())