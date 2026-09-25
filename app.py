import os

import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Text-to-Text AI",
    page_icon="🤖",
    layout="centered"
)


# --------------------------------------------------
# MODEL CONFIGURATION
# --------------------------------------------------

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

HF_TOKEN = os.getenv("HF_TOKEN")


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

@st.cache_resource
def load_model():

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        token=HF_TOKEN
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=(
            torch.float16
            if device == "cuda"
            else torch.float32
        ),
        device_map="auto",
        token=HF_TOKEN
    )

    model.eval()

    return tokenizer, model


# --------------------------------------------------
# TEXT GENERATION
# --------------------------------------------------

def generate_response(
    prompt,
    system_prompt="You are a helpful AI assistant.",
    max_new_tokens=200,
    temperature=0.7
):

    tokenizer, model = load_model()

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    # Convert messages into the model's chat format

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # Tokenize the input

    inputs = tokenizer(
        text,
        return_tensors="pt"
    )

    # Move tensors to the model device

    inputs = {
        key: value.to(model.device)
        for key, value in inputs.items()
    }

    # Generate response

    with torch.no_grad():

        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    # Remove the original prompt tokens

    input_length = inputs["input_ids"].shape[-1]

    generated_tokens = outputs[0][input_length:]

    # Decode generated tokens

    response = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    )

    return response.strip()


# --------------------------------------------------
# STREAMLIT INTERFACE
# --------------------------------------------------

st.title("Text-to-Text AI")

st.write(
    "Generate AI-powered text responses using "
    "the Qwen2.5-1.5B-Instruct model."
)

st.divider()


# --------------------------------------------------
# SIDEBAR SETTINGS
# --------------------------------------------------

with st.sidebar:

    st.header("Generation Settings")

    temperature = st.slider(
        "Temperature",
        min_value=0.1,
        max_value=1.5,
        value=0.7,
        step=0.1
    )

    max_tokens = st.slider(
        "Maximum New Tokens",
        min_value=50,
        max_value=500,
        value=200,
        step=50
    )


# --------------------------------------------------
# USER INPUT
# --------------------------------------------------

prompt = st.text_area(
    "Enter your prompt",
    placeholder="Example: Explain Artificial Intelligence in simple words.",
    height=150
)


# --------------------------------------------------
# GENERATE BUTTON
# --------------------------------------------------

if st.button("Generate Response", use_container_width=True):

    if not prompt.strip():

        st.warning("Please enter a prompt first.")

    else:

        try:

            with st.spinner("Generating response..."):

                response = generate_response(
                    prompt=prompt,
                    max_new_tokens=max_tokens,
                    temperature=temperature
                )

            st.subheader("AI Response")

            st.write(response)

        except Exception as e:

            st.error(
                "Something went wrong while generating the response."
            )

            st.exception(e)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Built with Python, Hugging Face Transformers, "
    "PyTorch and Streamlit."
)