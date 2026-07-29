import asyncio
import edge_tts

async def main():
    voices = await edge_tts.list_voices()
    english_male_voices = [
        v for v in voices 
        if v["Locale"].startswith("en") and v["Gender"] == "Male"
    ]
    for v in english_male_voices:
        print(f"{v['ShortName']} - {v['FriendlyName']}")

if __name__ == "__main__":
    asyncio.run(main())
