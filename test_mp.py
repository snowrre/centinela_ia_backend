import os
from dotenv import load_dotenv
import mercadopago

load_dotenv()

sdk = mercadopago.SDK(os.environ["MERCADOPAGO_ACCESS_TOKEN"])
preference_data = {
    "items": [
        {
            "title": "Test",
            "quantity": 1,
            "unit_price": float(100.0),
            "currency_id": "MXN"
        }
    ]
}
print(sdk.preference().create(preference_data))
