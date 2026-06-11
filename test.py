import google.generativeai as genai

genai.configure(api_key="AQ.Ab8RN6IeMX_HwAsAvxX37hxoWxsod7q3WkF_QMDI6V-pBN5FBQ")

models = genai.list_models()

for model in models:
    print(model.name)