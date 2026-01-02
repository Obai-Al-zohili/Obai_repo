import os
from crewai import Agent, LLM
from crewai_tools import ApifyActorsTool


def create_socialmedia_scraper_agent(llm: LLM):
    """
    Creates a Social Media Scraper agent that uses Apify Actors
    to scrape data from Twitter (X), Instagram, Facebook, and TikTok.
    Compatible with .execute_sync() workflow in app.py.
    """

    # Ensure token is available
    apify_token = os.getenv("APIFY_API_TOKEN")
    if not apify_token:
        raise ValueError("❌ APIFY_API_TOKEN is missing from environment variables.")

    # --- Initialize Apify actor tools with limits to avoid long heavy scrapes ---

    # X (Twitter)
    X_tool = ApifyActorsTool(
        actor_name="apidojo/twitter-scraper-lite",
        run_input={"run_input": {"maxItems": 15}},
        max_items=15
    )

    # Instagram — limit to the first page (≈12 posts)
    instagram_tool = ApifyActorsTool(
        actor_name="apify/instagram-scraper",
        run_input={
            "run_input": {
                "resultsLimit": 12,
                "shouldDownloadVideos": False,
                "shouldDownloadPhotos": False,
                "addParentData": False,
                "onlyPosts": True
            }
        },
        max_items=12
    )

    # Facebook — fixed: wrap input in "run_input"
    facebook_tool = ApifyActorsTool(
        actor_name="KoJrdxJCTtpon81KY",  # working Facebook Posts Scraper
        run_input={
            "run_input": {
                "startUrls": [
                    {"url": "https://www.facebook.com/YourPageName"}  # dynamically replaced later
                ],
                "resultsLimit": 10
            }
        },
        max_items=10
    )

    # TikTok — limit to few videos
    tiktok_tool = ApifyActorsTool(
        actor_name="clockworks/free-tiktok-scraper",
        run_input={"run_input": {"maxItems": 10}},
        max_items=10
    )

    # --- Return the configured agent ---
    return Agent(
        role="Social Media Scraper",
        goal=(
            "Extract concise textual and post content from Twitter, Instagram, "
            "Facebook, and TikTok, focusing on recent activity and summaries."
        ),
       
        llm=llm,
        tools=[X_tool, instagram_tool, facebook_tool, tiktok_tool],
        verbose=True
    )
