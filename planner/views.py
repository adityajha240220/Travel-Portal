from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import TravelQuery
from .serializers import TravelQuerySerializer

import os
import wikipedia
import google.generativeai as genai
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Configure Gemini with key from .env
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# --------------------------- HTML Views ---------------------------

class PlannerPageView(View):
    def get(self, request):
        return render(request, 'planner/planner.html')

class ResultPageView(View):
    def get(self, request):
        return render(request, 'planner/result.html')


# --------------------------- API: Generate Travel Plan ---------------------------

class GeneratePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        source = data.get('source')
        destination = data.get('destination')
        duration = data.get('duration')
        budget = data.get('budget')
        styles = data.get('styles')

        if not destination or not duration or not budget or not styles:
            return Response({'error': 'Missing required fields (destination, duration, budget, styles).'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            TravelQuery.objects.create(
                destination=destination,
                duration=duration,
                budget=budget,
                styles=styles,
            )
        except Exception as e:
            print(f"Error saving travel query: {e}")

        wikipedia_summary = ""
        try:
            wikipedia_summary = wikipedia.summary(destination, sentences=3)
        except wikipedia.exceptions.DisambiguationError:
            wikipedia_summary = f"Multiple results found for {destination}. Please be more specific."
        except wikipedia.exceptions.PageError:
            wikipedia_summary = f"No Wikipedia page found for {destination}."
        except Exception as e:
            wikipedia_summary = f"Error fetching Wikipedia summary: {str(e)}"

        # ✅ Gemini Travel Plan - Gemini 2.0 Flash Model
        travel_plan = "Failed to generate plan."
        try:
            prompt = f"""
            Create a detailed {duration}-day travel itinerary for {destination}.
            {f"Starting from {source}." if source else ""}
            Budget: {budget}. Style preferences: {styles}.
            Include key attractions, activities, and local tips.
            
            Here's some background information about {destination}: {wikipedia_summary}
            """

            model = genai.GenerativeModel('models/gemini-2.0-flash')  # ✅ Fixed model ID

            response = model.generate_content(prompt)
            travel_plan = response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
            return Response({'error': f'Failed to generate plan from AI: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'destination': destination,
            'summary': wikipedia_summary,
            'plan': travel_plan,
        }, status=status.HTTP_200_OK)


# --------------------------- API: Ask Follow-up Question ---------------------------

class AskQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get('question')
        plan_context = request.data.get('plan') 
        destination = request.data.get('destination')

        if not destination and plan_context:
            import re
            match = re.search(r'plan for ([\w\s,]+)!', plan_context, re.IGNORECASE)
            if match:
                destination = match.group(1).strip()

        if not question or not (destination or plan_context):
            return Response({'error': 'Missing question or sufficient context (destination/plan).'}, status=status.HTTP_400_BAD_REQUEST)

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

            model = genai.GenerativeModel('models/gemini-2.0-pro')  # ✅ Fixed here too

            response = model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            print(f"Gemini API error for question: {e}")
            answer = f"Error getting answer from AI: {str(e)}"

        return Response({'answer': answer}, status=status.HTTP_200_OK)
