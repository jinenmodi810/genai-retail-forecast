import streamlit as st
from inference.time_llm_forecastor import TimeLLMForecastor

st.title("🤖 TimeLLM Forecast Chatbot")

@st.cache_resource
def load_model():
    return TimeLLMForecastor()

model = load_model()

def chatbot_forecast_handler(user_question, model):
    # Dummy example to extract store, dept, pred_len from question with regex or parsing
    import re
    store_match = re.search(r"store\s*(\d+)", user_question, re.I)
    dept_match = re.search(r"department\s*(\d+)", user_question, re.I)
    pred_len_match = re.search(r"next\s*(\d+)\s*weeks?", user_question, re.I)

    store = int(store_match.group(1)) if store_match else 1
    dept = int(dept_match.group(1)) if dept_match else 1
    pred_len = int(pred_len_match.group(1)) if pred_len_match else model.config.pred_len

    # For demo, create dummy series of 60 points
    series = [100 + i for i in range(60)]

    # Predict using dynamic pred_len
    forecast = model.predict(series)

    # Format response
    response = (
        f"Forecast for Store {store}, Department {dept} "
        f"for next {pred_len} weeks:\n{forecast}"
    )
    return response

user_input = st.text_area("Ask your forecast question here:")
if st.button("Get Forecast"):
    if user_input.strip():
        try:
            answer = chatbot_forecast_handler(user_input, model)
            st.success(answer)
        except Exception as e:
            st.error(f"Error getting response: {e}")
    else:
        st.warning("Please enter a question.")