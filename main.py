import json
from sessions.session_manager import SessionManager
from agent.support_agent import create_agent
from dotenv import load_dotenv

load_dotenv()
print("dotenv works ✅")



# Load users from mock DB
with open("data/users.json") as f:
    USERS = json.load(f)


def find_user(email: str) -> dict | None:
    """Simulate a login lookup by email."""
    for user in USERS:
        if user["email"].lower() == email.lower():
            return user
    return None


def chat_loop(session, agent_executor):
    """Run the conversation loop for a logged-in user."""
    print(f"\nWelcome, {session.user_name}! Type 'quit' to logout, 'info' to see session info.\n")

    while True:
        user_input = input(f"[{session.user_name}] You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print(f"Goodbye, {session.user_name}!\n")
            break

        if user_input.lower() == "info":
            print(f"\n{session.summary()}\n")
            continue

        session.touch()  # update last active time
        response = agent_executor.invoke({"input": user_input})
        print(f"\nAgent: {response['output']}\n")


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

        # ── Login ──────────────────────────────
        if choice == "1":
            email = input("Enter your email: ").strip()
            user = find_user(email)

            if not user:
                print(f"No user found with email '{email}'. Try: alice@example.com or bob@example.com")
                continue

            # Reuse existing session or create a new one
            session = session_manager.get_session(user["user_id"])

            if session:
                print(f"[Session] Resuming existing session for {session.user_name}")
            else:
                session = session_manager.create_session(
                    user_id=user["user_id"],
                    user_name=user["name"],
                    tier=user["tier"]
                )

            # Create agent bound to this session
            agent_executor = create_agent(session)

            # Enter chat
            chat_loop(session, agent_executor)

            # After logout, ask to end session or keep it
            keep = input("Keep session alive for later? (y/n): ").strip().lower()
            if keep != "y":
                session_manager.end_session(user["user_id"])

        # ── List sessions ──────────────────────
        elif choice == "2":
            session_manager.list_sessions()

        # ── Exit ──────────────────────────────
        elif choice == "3":
            print("Shutting down. Goodbye!")
            break

        else:
            print("Invalid choice. Enter 1, 2, or 3.")


if __name__ == "__main__":
    main()