from backend.services.youtube_service import youtube_service
import sys

def main():
    print("Checking YouTube Authentication...")
    try:
        youtube = youtube_service.get_authenticated_service()
        if youtube:
            print("Successfully authenticated and generated token.pickle!")
    except Exception as e:
        print(f"Error during authentication: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
