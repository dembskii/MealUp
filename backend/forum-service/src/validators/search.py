from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum



class SearchCategory(str, Enum):
    """Available search categories"""
    ALL = "all"
    POSTS = "posts"
    RECIPES = "recipes"
    WORKOUTS = "workouts"
    AUTHORS = "authors"


class SearchSortBy(str, Enum):
    """Sort options for search results"""
    RELEVANCE = "relevance"
    NEWEST = "newest"
    TRENDING = "trending"
    MOST_LIKED = "most_liked"



class SearchQuery(BaseModel):
    """Schema for search query input"""
    query: str = Field(
        ..., 
        min_length=1, 
        max_length=200, 
        description="Search query string",
        examples=["tomato pasta", "leg workout"]
    )
    category: SearchCategory = Field(
        default=SearchCategory.ALL, 
        description="Category to search in - posts, recipes, workouts, authors or all"
    )
    tags: Optional[List[str]] = Field(
        default=None, 
        description="Filter by tags - list of tag names to include in results",
        examples=[["healthy", "quick"]]
    )
    author_id: Optional[str] = Field(
        default=None, 
        description="Filter by author ID - search only posts/recipes from specific author",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    sort_by: SearchSortBy = Field(
        default=SearchSortBy.RELEVANCE, 
        description="Sort results by - relevance, newest, trending or most_liked"
    )
    skip: int = Field(
        default=0, 
        ge=0, 
        description="Number of results to skip for pagination",
        examples=[0, 20, 40]
    )
    limit: int = Field(
        default=20, 
        ge=1, 
        le=100, 
        description="Maximum number of results to return - between 1 and 100",
        examples=[20, 50, 100]
    )
    
    model_config = ConfigDict(from_attributes=True)



class PostSearchResult(BaseModel):
    """Schema for post search result"""
    id: str = Field(
        ..., 
        description="Unique post ID",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    title: str = Field(
        ..., 
        description="Post title",
        examples=["Best Workout Tips for Beginners"]
    )
    content: str = Field(
        ..., 
        description="Post content preview or full content",
        examples=["Here are the best tips for starting your fitness journey..."]
    )
    author_id: str = Field(
        ..., 
        description="ID of the post author",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    author_name: Optional[str] = Field(
        default=None, 
        description="Author's display name",
        examples=["John Doe", "Jane Smith"]
    )
    tags: List[str] = Field(
        default=[], 
        description="List of tags associated with the post",
        examples=[["fitness", "beginner", "workout"]]
    )
    images: List[str] = Field(
        default=[], 
        description="List of image URLs attached to the post",
        examples=[["https://example.com/image1.jpg", "https://example.com/image2.jpg"]]
    )
    total_likes: int = Field(
        default=0, 
        ge=0, 
        description="Total number of likes on the post",
        examples=[42, 156, 1250]
    )
    views_count: int = Field(
        default=0, 
        ge=0, 
        description="Total number of views on the post",
        examples=[500, 2000, 10000]
    )
    comments_count: int = Field(
        default=0, 
        ge=0, 
        description="Total number of comments on the post",
        examples=[5, 23, 87]
    )
    trending_coefficient: float = Field(
        default=0.0, 
        ge=0.0, 
        description="Trending score calculated based on engagement metrics",
        examples=[0.5, 0.85, 1.2]
    )
    created_at: datetime = Field(
        ..., 
        description="Post creation timestamp",
        examples=["2026-01-10T14:30:00Z"]
    )
    updated_at: Optional[datetime] = Field(
        default=None, 
        description="Post last update timestamp",
        examples=["2026-01-15T09:15:00Z"]
    )
    relevance_score: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="Search relevance score between 0 and 1",
        examples=[0.95, 0.82, 0.65]
    )
    result_type: Literal["post"] = Field(
        default="post", 
        description="Result type identifier for this search result"
    )
    
    model_config = ConfigDict(from_attributes=True)



class AuthorSearchResult(BaseModel):
    """Schema for author search result"""
    id: str = Field(
        ..., 
        description="Unique author ID",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    name: str = Field(
        ..., 
        description="Author's display name",
        examples=["John Doe", "Jane Smith"]
    )
    posts_count: int = Field(
        default=0, 
        ge=0, 
        description="Total number of posts published by this author",
        examples=[5, 25, 100]
    )
    total_likes: int = Field(
        default=0, 
        ge=0, 
        description="Total number of likes across all author's posts",
        examples=[150, 500, 2000]
    )
    result_type: Literal["author"] = Field(
        default="author", 
        description="Result type identifier for this search result"
    )
    
    model_config = ConfigDict(from_attributes=True)



class RecipeSearchResult(BaseModel):
    """Schema for recipe search result (from MongoDB)"""
    id: str = Field(
        ..., 
        description="Unique recipe ID",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    name: str = Field(
        ..., 
        description="Recipe name",
        examples=["Tomato Pasta", "Grilled Salmon"]
    )
    description: Optional[str] = Field(
        default=None, 
        description="Recipe description or summary",
        examples=["A classic Italian pasta with fresh tomatoes and basil"]
    )
    author_id: Optional[str] = Field(
        default=None, 
        description="ID of the recipe creator",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    prep_time: Optional[int] = Field(
        default=None, 
        ge=0, 
        description="Preparation time in seconds",
        examples=[900, 1800, 3600]
    )
    difficulty: Optional[str] = Field(
        default=None, 
        description="Difficulty level of the recipe",
        examples=["easy", "medium", "hard"]
    )
    tags: List[str] = Field(
        default=[], 
        description="List of tags associated with the recipe",
        examples=[["healthy", "vegetarian", "gluten-free"]]
    )
    image_url: Optional[str] = Field(
        default=None, 
        description="URL to the recipe image",
        examples=["https://example.com/recipe-image.jpg"]
    )
    result_type: Literal["recipe"] = Field(
        default="recipe", 
        description="Result type identifier for this search result"
    )
    
    model_config = ConfigDict(from_attributes=True)



class WorkoutSearchResult(BaseModel):
    """Schema for workout search result (from MongoDB)"""
    id: str = Field(
        ..., 
        description="Unique workout ID",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    name: str = Field(
        ..., 
        description="Workout name",
        examples=["Full Body Strength", "HIIT Cardio Blast"]
    )
    description: Optional[str] = Field(
        default=None, 
        description="Workout description or overview",
        examples=["A comprehensive full-body strength training routine"]
    )
    author_id: Optional[str] = Field(
        default=None, 
        description="ID of the workout creator",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    duration: Optional[int] = Field(
        default=None, 
        ge=0, 
        description="Workout duration in seconds",
        examples=[1800, 3600, 5400]
    )
    difficulty: Optional[str] = Field(
        default=None, 
        description="Difficulty level of the workout",
        examples=["beginner", "intermediate", "advanced"]
    )
    workout_type: Optional[str] = Field(
        default=None, 
        description="Type of workout",
        examples=["cardio", "strength", "flexibility", "mixed"]
    )
    tags: List[str] = Field(
        default=[], 
        description="List of tags associated with the workout",
        examples=[["legs", "hypertrophy", "home-workout"]]
    )
    image_url: Optional[str] = Field(
        default=None, 
        description="URL to the workout image or thumbnail",
        examples=["https://example.com/workout-image.jpg"]
    )
    result_type: Literal["workout"] = Field(
        default="workout", 
        description="Result type identifier for this search result"
    )
    
    model_config = ConfigDict(from_attributes=True)



class SearchResultItem(BaseModel):
    """Union type for all search result types"""
    result_type: str = Field(
        ..., 
        description="Type of result - post, recipe, workout or author",
        examples=["post", "recipe", "workout", "author"]
    )
    data: dict = Field(
        ..., 
        description="Complete result data object containing all result fields"
    )
    relevance_score: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="Search relevance score between 0 and 1",
        examples=[0.95, 0.82, 0.65]
    )
    
    model_config = ConfigDict(from_attributes=True)



class SearchResponse(BaseModel):
    """Schema for complete search response"""
    query: str = Field(
        ..., 
        description="The search query string that was executed",
        examples=["tomato pasta", "leg workout"]
    )
    category: SearchCategory = Field(
        ..., 
        description="The category that was searched in",
        examples=["all", "posts", "recipes"]
    )
    total_results: int = Field(
        ..., 
        ge=0, 
        description="Total number of matching results across all categories",
        examples=[42, 156, 1250]
    )
    posts: List[PostSearchResult] = Field(
        default=[], 
        description="List of matching posts results",
        examples=[[]]
    )
    recipes: List[RecipeSearchResult] = Field(
        default=[], 
        description="List of matching recipes results",
        examples=[[]]
    )
    workouts: List[WorkoutSearchResult] = Field(
        default=[], 
        description="List of matching workouts results",
        examples=[[]]
    )
    authors: List[AuthorSearchResult] = Field(
        default=[], 
        description="List of matching authors results",
        examples=[[]]
    )
    has_more: bool = Field(
        default=False, 
        description="Indicates if there are more results available beyond the limit",
        examples=[True, False]
    )
    
    model_config = ConfigDict(from_attributes=True)



class TagSuggestion(BaseModel):
    """Schema for tag autocomplete suggestion"""
    tag: str = Field(
        ..., 
        description="The suggested tag name",
        examples=["fitness", "healthy", "beginner"]
    )
    count: int = Field(
        default=0, 
        ge=0, 
        description="Number of items using this tag",
        examples=[5, 23, 87]
    )
    
    model_config = ConfigDict(from_attributes=True)



class SearchSuggestionsResponse(BaseModel):
    """Schema for search autocomplete suggestions"""
    query: str = Field(
        ..., 
        description="The partial query string for which suggestions are provided",
        examples=["tom", "leg w"]
    )
    suggestions: List[str] = Field(
        default=[], 
        description="List of suggested search queries",
        examples=[["tomato pasta", "tomato sauce"]]
    )
    tags: List[TagSuggestion] = Field(
        default=[], 
        description="List of suggested tags matching the query",
        examples=[[]]
    )
    
    model_config = ConfigDict(from_attributes=True)