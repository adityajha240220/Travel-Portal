from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import TravelQuery
from .serializers import TravelQuerySerializer
from planner.utils.yacy_search import search_yacy
from scraper.playwright_scraper import fetch_html
from scraper.bs_parser import parse_summary
from django.views.generic import TemplateView
import asyncio
from playwright.async_api import async_playwright
import json 
import time
import random
import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import quote

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class PlannerPageView(View):
    def get(self, request):
        return render(request, 'planner/planner.html')

class ResultPageView(View):
    def get(self, request):
        return render(request, 'planner/result.html')

class PlannerPageView(TemplateView):
    template_name = 'planner/planner.html'

# --------------------------- Scraper Helpers ---------------------------

def _first_text_safe(el):
    try:
        return el.get_text(strip=True)
    except Exception:
        return ""

def _clean_price(text):
    if not text:
        return ""
    txt = re.sub(r'\s+', ' ', text).strip()
    return txt

def scrape_booking_hotels(destination, budget, max_results=3):
    """
    Scrape Booking.com's search results for top hotels.
    Returns list of dicts: {title, price, link}
    """
    results = []
    try:
        dest_q = quote(destination)
        budget_num_match = re.search(r'(\d[\d,.]*)', budget)
        if budget_num_match:
            budget_num = re.sub(r'[₹,]', '', budget_num_match.group(1))
            per_night_budget = int(budget_num) / 5
            url = f"https://www.booking.com/searchresults.html?ss={dest_q}&price_range_min=100&price_range_max={int(per_night_budget)}"
        else:
            url = f"https://www.booking.com/searchresults.html?ss={dest_q}"

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        html = fetch_html(url, headless=True, timeout=30000, user_agent=user_agent)
        if not html:
            return results

        soup = BeautifulSoup(html, "html.parser")

        cards = soup.find_all("div", class_=re.compile(r"d4924c9e74")) 
        if not cards:
            cards = soup.find_all("div", attrs={"data-testid": "property-card"})

        for card in cards[:max_results]:
            title_el = card.find("div", attrs={"data-testid": "title"}) or card.find("div", class_=re.compile(r"fcab3ed991"))
            title = _first_text_safe(title_el) if title_el else _first_text_safe(card.find("a")) or "Hotel"

            price_el = card.find("span", class_=re.compile(r"f6431b446a")) or card.find(attrs={"data-testid": "price-and-discounted-price"})
            price = _clean_price(_first_text_safe(price_el)) if price_el else ""

            link_el = card.find("a", href=True)
            link = link_el["href"] if link_el else url
            if link and link.startswith("/"):
                link = "https://www.booking.com" + link

            results.append({
                "title": title,
                "price": price,
                "link": link
            })

        return results
    except Exception as e:
        print(f"Booking scrape error: {e}")
        return results

def scrape_skyscanner_flights(origin, destination, max_results=3):
    return []

def scrape_redbus_buses(origin, destination, max_results=3):
    return []

def scrape_live_prices(destination, budget, source=None):
    """
    Aggregate scrapers for multiple categories and return their top results.
    """
    data = {
        "hotels": [],
        "flights": [],
        "buses": [],
        "restaurants": []
    }
    try:
        try:
            hotels = scrape_booking_hotels(destination, budget, max_results=3)
            data["hotels"] = hotels
        except Exception as e:
            print(f"hotel scraper error: {e}")

    except Exception as e:
        print(f"scrape_live_prices aggregate error: {e}")

    return data

def generate_booking_links(source, destination, budget, duration):
    """
    Generates dynamic, clickable links for various booking websites
    based on the user's destination, source, budget, and duration.
    Uses generic search-based links for any destination.
    """
    destination_str = quote(destination)
    source_str = quote(source) if source else ""
    
    budget_num_match = re.search(r'(\d[\d,.]*)', budget)
    if budget_num_match and duration:
        budget_num = re.sub(r'[₹,]', '', budget_num_match.group(1))
        per_night_budget = int(budget_num) / int(duration)
        budget_str = str(int(per_night_budget))
    else:
        budget_str = "5000"
    
    # Generic booking links for any destination
    links = {
        "Hotels": {
            "Booking.com": f"https://www.booking.com/searchresults.html?ss={destination_str}&price_range_min=100&price_range_max={budget_str}",
            "Airbnb": f"https://www.airbnb.com/s/{destination_str}/homes",
            "Search Hotels": f"https://www.google.com/search?q={destination_str}+hotels+booking"
        },
        "Flights": {
            "Google Flights": f"https://www.google.com/flights?q=flights+from+{source_str}+to+{destination_str}",
            "Skyscanner": f"https://www.skyscanner.com/transport/flights/{source_str.lower()}/{destination_str.lower()}/",
            "Search Flights": f"https://www.google.com/search?q=flights+to+{destination_str}"
        },
        "Transport": {
            "Rome2rio": f"https://www.rome2rio.com/map/{source_str}/{destination_str}",
            "Google Maps": f"https://www.google.com/maps/search/transport+in+{destination_str}",
            "Search Transport": f"https://www.google.com/search?q={destination_str}+transport+options"
        },
        "Restaurants": {
            "TripAdvisor": f"https://www.tripadvisor.com/Search?q={destination_str}+restaurants",
            "Yelp": f"https://www.yelp.com/search?find_desc=restaurants&find_loc={destination_str}",
            "Search Restaurants": f"https://www.google.com/search?q={destination_str}+restaurants"
        }
    }
    
    return links

def format_itinerary_text(plan_text):
    if not plan_text:
        return ""
    
    plan_text = re.sub(r'^(Day \d+:.+)', r'<h3>\1</h3>', plan_text, flags=re.MULTILINE)
    plan_text = re.sub(r'^(Assumptions:|Budget Breakdown:|Important Considerations:)', r'<h3>\1</h3>', plan_text, flags=re.MULTILINE)
    plan_text = re.sub(r'^\s*(\*\*[\w\s]+\*\*):', r'<h4>\1</h4>', plan_text, flags=re.MULTILINE)
    plan_text = re.sub(r'^\s*(\*\*[\w\s]+\*\*)$', r'<h4>\1</h4>', plan_text, flags=re.MULTILINE)

    lines = plan_text.split('\n')
    formatted_lines = []
    in_list = False
    for line in lines:
        if line.strip().startswith('*') or line.strip().startswith('-'):
            if not in_list:
                formatted_lines.append('<ul>')
                in_list = True
            line = '<li>' + line.strip('*- ').strip() + '</li>'
            formatted_lines.append(line)
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(line)
    if in_list:
        formatted_lines.append('</ul>')
    plan_text = '\n'.join(formatted_lines)
    
    plan_text = plan_text.replace('\n\n', '</p><p>')
    plan_text = plan_text.replace('</p><p><h3>', '<h3>').replace('</p><p><h4>', '<h4>').replace('</p><p><ul>', '<ul>')
    plan_text = f"<p>{plan_text}</p>"
    plan_text = plan_text.replace("**", "<strong>")
    
    return plan_text

def embed_booking_links(plan_text, links, destination):
    """
    Embeds links for specific places in the plan text and returns a separate section for booking links.
    Uses Google search for dynamic place links.
    """
    if not links:
        return plan_text, ""

    # Extract potential place names from the plan text dynamically
    # Simple approach: find capitalized phrases that could be place names
    words = re.findall(r'\b(?:[A-Z][a-z]*\s*){2,}\b', plan_text)
    specific_names = list(set(words))  # Remove duplicates

    # Embed links for specific place names
    for name in sorted(specific_names, key=len, reverse=True):
        pattern = r'\b' + re.escape(name) + r'\b(?!<\/a>)'
        url = f"https://www.google.com/search?q={quote(name)}+{destination}+official+site"
        replacement = f'<a href="{url}" target="_blank" style="color: #03dac6; text-decoration: none; font-weight: bold;">{name}</a>'
        plan_text = re.sub(pattern, replacement, plan_text, flags=re.IGNORECASE, count=1)

    # Create a separate booking links section
    booking_section = "<h3>Booking Links</h3><ul>"
    for category, sites in links.items():
        booking_section += f"<li><strong>{category}</strong><ul>"
        for site_name, url in sites.items():
            booking_section += f'<li><a href="{url}" target="_blank" style="color: #03dac6; text-decoration: none;">{site_name}</a></li>'
        booking_section += "</ul></li>"
    booking_section += "</ul>"

    return plan_text, booking_section

class GeneratePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data or {}
        source = data.get('source')
        destination = data.get('destination')
        duration = data.get('duration')
        budget = data.get('budget')
        styles = data.get('styles')

        if not destination or not duration or not budget or not styles:
            return Response({'error': 'Missing required fields (destination, duration, budget, styles).'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            TravelQuery.objects.create(
                destination=destination,
                duration=duration,
                budget=budget,
                styles=styles,
            )
        except Exception as e:
            print(f"Error saving travel query: {e}")

        # --------------------------- Context Gathering (YaCy) ---------------------------
        try:
            results = search_yacy(destination)
            if results and 'error' not in results[0]:
                summary_parts = []
                for item in results[:3]:
                    try:
                        html = fetch_html(item['link'])
                        summary = parse_summary(html) if html else "Could not fetch content."
                        summary_parts.append(f"{item['title']}: {summary}")
                    except Exception as exc:
                        print(f"Error fetching/parsing {item['link']}: {exc}")
                        summary_parts.append(f"{item['title']}: Could not fetch content.")
                info_snippet = "\n\n".join(summary_parts)
            else:
                info_snippet = "Sorry, I couldn't find much info at the moment."
        except Exception as e:
            print(f"YaCy error: {e}")
            info_snippet = "Error fetching info from YaCy."

        # --------------------------- Gemini Travel Plan Generation ---------------------------
        travel_plan = "Failed to generate plan."
        try:
            prompt = f"""
            Create a detailed {duration}-day travel itinerary for {destination}, starting from {source}.
            Budget: {budget}. Travel Style: {styles}.
            Include key attractions, local activities, and tips.
            
            When suggesting transportation, mention the names of local bus companies, train services, or popular flight aggregators. Also mention specific airport train services if relevant.
            
            When suggesting food or restaurants, mention specific popular local places or chains relevant to {destination}.
            
            Format the itinerary with clear headings like "Day 1:", "Assumptions:", "Budget Breakdown:", and use bullet points for lists.
            Ensure the text is rich with keywords like 'bus', 'flight', 'hotel', 'train', and specific restaurant names within the text of the itinerary.

            Here's some background information about {destination}: {info_snippet}
            """

            model = genai.GenerativeModel('models/gemini-2.0-flash')
            response = model.generate_content(prompt)
            travel_plan = response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
            return Response({'error': f'Failed to generate plan from AI: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # --------------------------- Formatting and Embedding Links ---------------------------
        booking_links = generate_booking_links(source, destination, budget, duration)
        
        formatted_plan_text = format_itinerary_text(travel_plan)
        final_plan, booking_section = embed_booking_links(formatted_plan_text, booking_links, destination)
        final_plan += booking_section  # Append booking links section to the itinerary

        # --------------------------- Live Scraping ---------------------------
        live_data = {}
        try:
            live_data = scrape_live_prices(destination, budget, source)
        except Exception as e:
            print(f"Live scraping overall error: {e}")
            live_data = {"hotels": [], "flights": [], "buses": [], "restaurants": []}

        # --------------------------- Response ---------------------------
        return Response({
            'destination': destination,
            'summary': info_snippet,
            'plan': final_plan,
            'live_data': live_data,
            'links': booking_links
        }, status=status.HTTP_200_OK)

class AskQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get('question')
        plan_context = request.data.get('plan')
        destination = request.data.get('destination')

        if not destination and plan_context:
            match = re.search(r'plan for ([\w\s,]+)!', plan_context, re.IGNORECASE)
            if match:
                destination = match.group(1).strip()

        if not question or not (destination or plan_context):
            return Response({'error': 'Missing question or sufficient context (destination/plan).'},
                            status=status.HTTP_400_BAD_REQUEST)

        answer = "Sorry, I couldn't provide an answer."
        try:
            prompt = f"""
            Given the following travel plan context:
            ---
            {plan_context}
            ---

            And the user's question: "{question}"

            Please provide a concise and helpful answer based on the context or general travel knowledge about {destination if destination else 'the destination in the plan'}.
            """

            model = genai.GenerativeModel('models/gemini-2.0-pro')
            response = model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            print(f"Gemini API error for question: {e}")

            # Fallback to YaCy + Playwright + BeautifulSoup
            try:
                results = search_yacy(question)
                if results and 'error' not in results[0]:
                    summary_parts = []
                    for item in results[:3]:
                        try:
                            html = fetch_html(item['link'])
                            summary = parse_summary(html)
                            summary_parts.append(f"{item['title']}: {summary}")
                        except Exception as exc:
                            print(f"Error fetching/parsing {item['link']}: {exc}")
                            summary_parts.append(f"{item['title']}: Could not fetch content.")
                    answer = "\n\n".join(summary_parts)
                else:
                    answer = "Sorry, I couldn't find anything relevant at the moment."
            except Exception as fallback_e:
                print(f"YaCy fallback error: {fallback_e}")
                answer = "Error fetching fallback answer from YaCy."

        return Response({'answer': answer}, status=status.HTTP_200_OK)

class LiveDealsView(APIView):
    permission_classes = [IsAuthenticated]

    async def scrape_deals(self, location):
        url = f"https://www.booking.com/searchresults.html?ss={location}"
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(5000)  # wait for content to load
            html = await page.content()
            await browser.close()

        soup = BeautifulSoup(html, "html.parser")
        hotels = []

        for item in soup.select("div[data-testid='property-card']")[:5]:  # Top 5 results
            name = item.select_one("div[data-testid='title']").get_text(strip=True) if item.select_one("div[data-testid='title']") else "No Name"
            price = item.select_one("span[data-testid='price-and-discounted-price']").get_text(strip=True) if item.select_one("span[data-testid='price-and-discounted-price']") else "Price not available"
            link = item.select_one("a[data-testid='title-link']")
            link_url = f"https://www.booking.com{link['href']}" if link else "#"

            hotels.append({
                "name": name,
                "price": price,
                "url": link_url
            })

        return hotels

    def post(self, request):
        location = request.data.get("location", "New Delhi")
        deals = asyncio.run(self.scrape_deals(location))
        return Response({"location": location, "deals": deals})