"""Command-line interface for TwineWriter."""
from dotenv import load_dotenv

from .workflow import run_twinewriter


def main():
    load_dotenv()

    print("\n🚀 TwineWriter Interactive Mode")
    print("=" * 70)

    topic = input("Enter your topic: ").strip()
    print("\nTone options: professional, educational, witty, marketing, storytelling, casual")
    tone = input("Enter tone (default: professional): ").strip() or "professional"
    base_content = input("Base content (optional, press Enter to skip): ").strip()

    result = run_twinewriter(topic, tone, base_content)

    if result:
        import json

        print("\n" + "=" * 70)
        print("✅ FINAL OUTPUT (JSON):")
        print("=" * 70)
        print(json.dumps(result, indent=2))
        print("\n✅ Content ready for posting!")
    else:
        print("\n❌ No final output generated.")


if __name__ == "__main__":
    main()
