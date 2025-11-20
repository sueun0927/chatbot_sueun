import streamlit as st
from openai import OpenAI
from typing import List, Dict

st.set_page_config(page_title="아우터 추천 챗봇", page_icon="🧥")

st.title("🧥 아우터 추천 챗봇")
st.write(
    "아우터(자켓/코트)를 추천하고 대화를 이어가는 간단한 챗봇입니다."
)

# 기본 시스템 프롬프트(편집 UI의 placeholder로 사용)
default_system_prompt = (
    "You are a helpful and friendly fashion assistant specialized in recommending outerwear (jackets, coats, blazers, parkas, etc.). "
    "When given a user's context (season, temperature, occasion, personal style), recommend 1-3 suitable outerwear options with short explanations and styling tips. "
    "Ask one follow-up question if more information is needed. Keep suggestions concise and practical."
)

# 시스템 프롬프트 편집창: 제목 바로 아래에 노출
placeholder_text = st.session_state.get("system_prompt", default_system_prompt) if "system_prompt" in st.session_state else default_system_prompt
st.text_area("시스템 프롬프트 편집 (챗봇 동작을 제어합니다)", value="", placeholder=placeholder_text, key="system_prompt_input", height=180)
if st.button("시스템 프롬프트 적용"):
    new_prompt = st.session_state.get("system_prompt_input", "").strip()
    if new_prompt == "":
        st.session_state["system_prompt"] = default_system_prompt
    else:
        st.session_state["system_prompt"] = new_prompt
    st.success("시스템 프롬프트가 적용되었습니다.")
    # 이미 대화 이력이 있으면 첫 메시지(시스템)를 교체
    if "messages" in st.session_state and len(st.session_state.messages) > 0 and st.session_state.messages[0].get("role") == "system":
        st.session_state.messages[0]["content"] = st.session_state["system_prompt"]

# Load API key from Streamlit secrets (no user input box)
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if not openai_api_key:
    st.error(
        "OpenAI API 키가 설정되어 있지 않습니다. `.streamlit/secrets.toml`에 `OPENAI_API_KEY`를 추가해주세요."
    )
else:
    client = OpenAI(api_key=openai_api_key)

    # Initialize session messages with a system prompt that guides the assistant's behavior
    if "messages" not in st.session_state:
        initial_sys = st.session_state.get("system_prompt", default_system_prompt)
        st.session_state.messages = [
            {"role": "system", "content": initial_sys}
        ]

    # Render chat history
    for msg in st.session_state.messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        with st.chat_message(role):
            st.markdown(content)

    # Chat input for user messages (no API key input)
    prompt = st.chat_input("아우터 추천을 받아보세요 — 예: '봄 나들이에 가기 좋은 가벼운 아우터 추천해줘'")
    if prompt:
        # Append user message and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare messages for the API call
        api_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        # Call OpenAI Chat Completions with gpt-4o-mini
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=api_messages,
                max_tokens=512,
                temperature=0.8,
            )

            # Extract assistant reply robustly
            assistant_reply = ""
            try:
                assistant_reply = response.choices[0].message.content
            except Exception:
                try:
                    assistant_reply = response.choices[0].message["content"]
                except Exception:
                    assistant_reply = str(response)

        except Exception as e:
            assistant_reply = f"오류가 발생했습니다: {e}"

        # Display and save assistant reply
        with st.chat_message("assistant"):
            st.markdown(assistant_reply)
        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
