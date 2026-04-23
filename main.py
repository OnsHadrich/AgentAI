from dotenv import load_dotenv
load_dotenv()

import json
import os
from sessions.session_manager import SessionManager
from agent.support_agent import create_agent

with open("data/users.json") as f:
    USERS = json.load(f)


def find_user(email: str) -> dict | None:
    for user in USERS:
        if user["email"].lower() == email.lower():
            return user
    return None


def chat_loop(session, agent):
    print(f"\nWelcome, {session.user_name}! Type 'quit' to logout, 'info' to see session info.\n")

    while True:
        user_input = input(f"[{session.user_name}] You: ").strip()
        if not user_input: continue
        if user_input.lower() == "quit": break
        if user_input.lower() == "info":
            print(f"\n{session.summary()}\n")
            continue

        session.touch()

        try:
            # ✅ LangGraph v1 format
            result = agent.invoke(
                {"messages": [("user", user_input)]},
                config={"configurable": {"thread_id": f"{session.user_id}-clean"}} # keeps history per user
            )
            
            # Get the last AI message (no tool calls shown)
            last_message = result["messages"][-1]
            print(f"\nAgent: {last_message.content}\n")

        except Exception as e:
            print(f"\n[Error] {e}\n")


def main():
    session_manager = SessionManager()

    print("=" * 40)
    print("   ShopAI Customer Support")
    print("=" * 40)

    while True:
        print("\nOptions:")
        print("  1. Login")
        print("  2. List active sessions")
        print("  3. Exit")

        choice = input("\nChoose: ").strip()

        if choice == "1":
            email = input("Enter your email: ").strip()
            user = find_user(email)

            if not user:
                print(f"No user found. Try: alice@example.com or bob@example.com")
                continue

            session = session_manager.get_session(user["user_id"])

            if session:
                print(f"[Session] Resuming existing session for {session.user_name}")
            else:
                session = session_manager.create_session(
                    user_id=user["user_id"],
                    user_name=user["name"],
                    tier=user["tier"]
                )

            agent = create_agent(session)   # ← now returns single chain, not tuple
            chat_loop(session, agent)

            keep = input("Keep session alive for later? (y/n): ").strip().lower()
            if keep != "y":
                session_manager.end_session(user["user_id"])

        elif choice == "2":
            session_manager.list_sessions()

        elif choice == "3":
            print("Shutting down. Goodbye!")
            break

        else:
            print("Invalid choice. Enter 1, 2, or 3.")


if __name__ == "__main__":
    main()