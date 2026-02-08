
import sys
import os

# Add custom_components to path
sys.path.append(os.path.abspath("."))

try:
    print("Testing import of custom_components.whatsapp...")
    import custom_components.whatsapp as whatsapp
    print("Successfully imported custom_components.whatsapp")

    print("Testing import of custom_components.whatsapp.config_flow...")
    import custom_components.whatsapp.config_flow as config_flow
    print("Successfully imported custom_components.whatsapp.config_flow")

    print("Checking for ConfigFlow in config_flow module...")
    if hasattr(config_flow, "ConfigFlow"):
        print("Found ConfigFlow class")
    else:
        print("Mising ConfigFlow class!")

    print("Checking for WhatsAppApiClient in whatsapp namespace...")
    if hasattr(whatsapp, "WhatsAppApiClient"):
        print("Found WhatsAppApiClient in whatsapp namespace")
    else:
        print("Missing WhatsAppApiClient in whatsapp namespace!")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
