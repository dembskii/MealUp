"use client";

import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import RecipeList from "../components/Recipe/RecipeList";
import RecipeCreator from "../components/Recipe/RecipeCreator";
import LandingPage from "../components/LandingPage";
import { Loader2 } from "lucide-react";

export default function RecipesPage() {
  const { isLoading, isAuthenticated } = useAuth();
  const [showCreator, setShowCreator] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-7 h-7 animate-spin text-brand-500" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LandingPage />;
  }

  const handleAddRecipe = () => {
    setShowCreator(true);
  };

  const handleCloseCreator = () => {
    setShowCreator(false);
  };

  const handleRecipeCreated = (newRecipe) => {
    // Trigger refresh of recipe list
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-8">
          🍽️ Recipe Collection
        </h1>

        <RecipeList key={refreshKey} onAddRecipe={handleAddRecipe} />

        {showCreator && (
          <RecipeCreator
            onClose={handleCloseCreator}
            onRecipeCreated={handleRecipeCreated}
          />
        )}
      </div>
    </div>
  );
}
