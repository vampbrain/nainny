"""Application entrypoint: optional FastAPI app and create_app factory.

Importing this module will not fail if FastAPI isn't installed. Use
create_app() to construct the ASGI app when running the server.
"""

from typing import Optional


def create_app() -> object:
	"""Create and return a FastAPI app instance.

	This function imports FastAPI lazily so the package can be imported in
	environments where FastAPI is not installed (e.g. some test environments).
	"""
	try:
		from fastapi import FastAPI
		from fastapi.responses import JSONResponse
	except Exception as e:  # pragma: no cover - external dependency
		raise RuntimeError("FastAPI is required to create the web application") from e

	from app.core.database import init_db

	app = FastAPI(title="Nainny - Narrative Intelligence")

	@app.on_event("startup")
	def on_startup():
		init_db()

	@app.get("/health")
	def health():
		return JSONResponse({"status": "ok"})

	@app.get("/seed-culture")
	def seed_culture():
		try:
			from app.services.init_db import seed_indian_cultural_data

			seed_indian_cultural_data()
			return JSONResponse({"seeded": True})
		except Exception as exc:  # pragma: no cover - surface errors during demo
			return JSONResponse({"seeded": False, "error": str(exc)}, status_code=500)

	# Adapt story endpoint - lazy imports so tests can run without ML deps
	from pydantic import BaseModel


	class AdaptStoryRequest(BaseModel):
		story_id: int
		target_culture: str
		target_age: str

	@app.post("/adapt-story")
	def adapt_story(req: AdaptStoryRequest):
		from app.core.database import get_db
		from app.models.story import Story
		# lazy import ML services
		try:
			from app.services.adaptive_storyteller import AdaptiveStoryteller
			from app.services.story_evaluator import StoryEvaluator
		except Exception as e:
			# If ML deps not installed, surface a helpful error
			return JSONResponse({"error": "ML dependencies not installed or import failed", "detail": str(e)}, status_code=500)

		# simple DB access
		with get_db() as db:
			story = db.query(Story).filter(Story.id == req.story_id).first()
			if not story:
				return JSONResponse({"error": "Story not found"}, status_code=404)

		storyteller = AdaptiveStoryteller()
		evaluator = StoryEvaluator()

		# concept_features could be derived by cultural analyzer; keep empty for now
		concept_features = {}

		adapted_text = storyteller.adapt(
			story_text=story.content,
			target_culture=req.target_culture,
			target_age=req.target_age,
			concept_features=concept_features,
		)

		score = evaluator.composite_score(story.content, adapted_text, req.target_culture)

		return JSONResponse({
			"story_id": story.id,
			"target_culture": req.target_culture,
			"target_age": req.target_age,
			"adapted_story": adapted_text,
			"score": score,
		})

	return app


# Do not create the FastAPI `app` at module import time. Call `create_app()`
# explicitly where needed (e.g. in an entrypoint or test). Creating the app
# at import time caused models and DB metadata to be registered before tests
# could control DB setup which led to duplicate registrations and index errors.

