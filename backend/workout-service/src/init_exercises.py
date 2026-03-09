# backend/workout-service/src/init_exercises.py
"""
Initialize MongoDB with 120+ real exercises for the workout service.
Deterministic UUIDs are generated from exercise names so that other
seed scripts can reference them reliably.

Run from the src/ directory:
    python init_exercises.py
"""

import asyncio
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db.mongodb import connect_to_mongodb, disconnect_from_mongodb, get_database
from core.config import settings
from models.model import Exercise, BodyPart, Advancement, ExerciseCategory

# ---------------------------------------------------------------------------
# Deterministic ID generation
# ---------------------------------------------------------------------------
EXERCISE_NS = uuid.UUID("b4cc290f-9cf0-4999-a013-bdf5e7644103")


def make_exercise_id(name: str) -> str:
    """Generate a deterministic UUID-5 from an exercise name."""
    return str(uuid.uuid5(EXERCISE_NS, name.lower().strip()))


# ---------------------------------------------------------------------------
# Shorthand helpers
# ---------------------------------------------------------------------------
BP = BodyPart
ADV = Advancement
CAT = ExerciseCategory


def ex(name, body_part, advancement, category, description, hints):
    """Shorthand helper to build an exercise tuple."""
    return (name, body_part, advancement, category, description, hints)


# ---------------------------------------------------------------------------
# Exercise data — grouped by primary body part
# ---------------------------------------------------------------------------

CHEST_EXERCISES = [
    ex("Barbell Bench Press", BP.CHEST, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Compound pressing movement targeting the chest, front delts, and triceps. Performed lying on a flat bench.",
       ["Keep feet flat on the floor", "Retract shoulder blades", "Lower bar to mid-chest", "Drive through the heels"]),
    ex("Incline Barbell Bench Press", BP.CHEST, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Upper chest-focused pressing movement on a 30-45 degree inclined bench.",
       ["Set bench to 30-45 degrees", "Lower bar to upper chest", "Keep elbows at 45-degree angle"]),
    ex("Decline Barbell Bench Press", BP.CHEST, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Lower chest-focused pressing movement on a declined bench.",
       ["Secure legs under the pads", "Lower bar to lower chest", "Don't flare elbows excessively"]),
    ex("Dumbbell Bench Press", BP.CHEST, ADV.BEGINNER, CAT.STRENGTH,
       "Pressing movement with dumbbells allowing greater range of motion than barbell.",
       ["Keep dumbbells in line with mid-chest", "Control the eccentric phase", "Squeeze chest at the top"]),
    ex("Incline Dumbbell Bench Press", BP.CHEST, ADV.BEGINNER, CAT.STRENGTH,
       "Upper chest-focused dumbbell press on an incline bench.",
       ["Set bench to 30-45 degrees", "Keep wrists neutral", "Full range of motion"]),
    ex("Dumbbell Fly", BP.CHEST, ADV.BEGINNER, CAT.STRENGTH,
       "Isolation exercise stretching and contracting the chest through a wide arc.",
       ["Keep a slight bend in elbows", "Lower until you feel a stretch", "Squeeze at the top"]),
    ex("Cable Crossover", BP.CHEST, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Cable-based fly movement providing constant tension throughout the range of motion.",
       ["Step slightly forward", "Keep a slight bend in elbows", "Cross hands at the bottom for peak contraction"]),
    ex("Push-Up", BP.CHEST, ADV.BEGINNER, CAT.CALISTHENICS,
       "Classic bodyweight pressing exercise targeting chest, shoulders, and triceps.",
       ["Keep body in a straight line", "Lower chest to the floor", "Full lockout at the top"]),
    ex("Diamond Push-Up", BP.CHEST, ADV.INTERMEDIATE, CAT.CALISTHENICS,
       "Close-grip push-up variation emphasizing triceps and inner chest.",
       ["Place hands close together forming a diamond shape", "Keep elbows close to the body", "Control the descent"]),
    ex("Chest Dip", BP.CHEST, ADV.INTERMEDIATE, CAT.CALISTHENICS,
       "Dip variation leaning forward to emphasize the lower chest.",
       ["Lean forward at about 30 degrees", "Lower until upper arms are parallel to the floor", "Don't lock out aggressively"]),
    ex("Machine Chest Press", BP.CHEST, ADV.BEGINNER, CAT.STRENGTH,
       "Machine-guided pressing movement, great for beginners or high-rep finisher sets.",
       ["Adjust seat height so handles are at chest level", "Push evenly with both arms", "Control the return"]),
    ex("Pec Deck Machine", BP.CHEST, ADV.BEGINNER, CAT.STRENGTH,
       "Machine-based fly movement isolating the pectoral muscles.",
       ["Keep a slight bend in elbows", "Squeeze at the center", "Control the eccentric"]),
]

BACK_EXERCISES = [
    ex("Barbell Deadlift", BP.BACK, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Fundamental compound lift working the entire posterior chain.",
       ["Keep back neutral", "Drive through the heels", "Keep bar close to body", "Hinge at the hips"]),
    ex("Conventional Deadlift", BP.BACK, ADV.INTERMEDIATE, CAT.POWERLIFTING,
       "Standard deadlift stance with hands outside the knees.",
       ["Feet hip-width apart", "Grip just outside knees", "Brace your core", "Lock out hips and knees together"]),
    ex("Sumo Deadlift", BP.BACK, ADV.INTERMEDIATE, CAT.POWERLIFTING,
       "Wide-stance deadlift variation emphasizing quads and inner thighs alongside back.",
       ["Wide stance with toes pointed out", "Grip inside the knees", "Push knees out", "Keep torso more upright"]),
    ex("Pull-Up", BP.BACK, ADV.INTERMEDIATE, CAT.CALISTHENICS,
       "Classic bodyweight pulling exercise targeting lats and biceps.",
       ["Full dead hang at bottom", "Pull until chin clears the bar", "Control the descent", "Avoid kipping"]),
    ex("Chin-Up", BP.BACK, ADV.INTERMEDIATE, CAT.CALISTHENICS,
       "Supinated-grip pull-up variation placing more emphasis on biceps.",
       ["Use underhand grip", "Pull chin above the bar", "Squeeze shoulder blades together"]),
    ex("Lat Pulldown", BP.BACK, ADV.BEGINNER, CAT.STRENGTH,
       "Cable exercise mimicking the pull-up motion with adjustable resistance.",
       ["Pull bar to upper chest", "Lean back slightly", "Squeeze lats at the bottom", "Control the return"]),
    ex("Barbell Row", BP.BACK, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Compound rowing movement building back thickness.",
       ["Hinge forward at 45 degrees", "Pull bar to lower chest", "Squeeze shoulder blades", "Keep core tight"]),
    ex("Dumbbell Row", BP.BACK, ADV.BEGINNER, CAT.STRENGTH,
       "Unilateral rowing movement allowing focus on each side independently.",
       ["Support with opposite hand and knee on bench", "Pull dumbbell to hip", "Keep back flat"]),
    ex("Seated Cable Row", BP.BACK, ADV.BEGINNER, CAT.STRENGTH,
       "Cable rowing exercise targeting the middle back.",
       ["Sit upright", "Pull handle to lower chest", "Squeeze shoulder blades together", "Don't lean back excessively"]),
    ex("T-Bar Row", BP.BACK, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Compound rowing variation using a landmine or T-bar apparatus.",
       ["Keep chest against the pad if available", "Pull to the chest", "Squeeze at the top"]),
    ex("Face Pull", BP.BACK, ADV.BEGINNER, CAT.STRENGTH,
       "Cable exercise targeting rear delts and upper back, excellent for shoulder health.",
       ["Use rope attachment at face height", "Pull to ears", "Externally rotate at the end", "Keep elbows high"]),
    ex("Hyperextension", BP.BACK, ADV.BEGINNER, CAT.STRENGTH,
       "Lower back isolation exercise performed on a hyperextension bench.",
       ["Cross arms over chest or behind head", "Hinge at the hips", "Don't hyperextend the spine"]),
]

SHOULDER_EXERCISES = [
    ex("Overhead Press", BP.SHOULDERS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Standing barbell press overhead, a fundamental shoulder strength builder.",
       ["Start at collarbone level", "Press straight up", "Lock out overhead", "Keep core tight"]),
    ex("Dumbbell Shoulder Press", BP.SHOULDERS, ADV.BEGINNER, CAT.STRENGTH,
       "Seated or standing dumbbell press for balanced shoulder development.",
       ["Press dumbbells overhead", "Don't clang them together at the top", "Control the descent"]),
    ex("Arnold Press", BP.SHOULDERS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Rotational dumbbell press hitting all three deltoid heads.",
       ["Start with palms facing you", "Rotate as you press up", "Full rotation at the top"]),
    ex("Lateral Raise", BP.SHOULDERS, ADV.BEGINNER, CAT.STRENGTH,
       "Isolation exercise targeting the lateral (side) deltoid.",
       ["Slight bend in elbows", "Raise to shoulder height", "Lead with the elbows", "Control the descent"]),
    ex("Front Raise", BP.SHOULDERS, ADV.BEGINNER, CAT.STRENGTH,
       "Isolation exercise targeting the anterior (front) deltoid.",
       ["Keep arms nearly straight", "Raise to eye level", "Don't swing the weight"]),
    ex("Reverse Fly", BP.SHOULDERS, ADV.BEGINNER, CAT.STRENGTH,
       "Rear deltoid isolation, performed bent over or on a machine.",
       ["Hinge forward at hips", "Raise arms out to the sides", "Squeeze shoulder blades", "Keep a slight bend in elbows"]),
    ex("Upright Row", BP.SHOULDERS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Barbell or dumbbell pulling movement targeting delts and traps.",
       ["Pull to chin height", "Keep elbows above hands", "Use a wide grip to reduce shoulder impingement"]),
    ex("Cable Lateral Raise", BP.SHOULDERS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Lateral raise performed with a cable for constant tension throughout.",
       ["Stand sideways to the cable", "Raise arm to shoulder height", "Control the return"]),
    ex("Pike Push-Up", BP.SHOULDERS, ADV.INTERMEDIATE, CAT.CALISTHENICS,
       "Bodyweight pressing exercise targeting shoulders by elevating the hips.",
       ["Form an inverted V with your body", "Lower head toward the floor", "Press back up to start"]),
    ex("Handstand Push-Up", BP.SHOULDERS, ADV.EXPERT, CAT.CALISTHENICS,
       "Advanced bodyweight press performed in a handstand position against a wall.",
       ["Kick up against a wall", "Lower head to the floor", "Press back up", "Keep core extremely tight"]),
]

BICEPS_EXERCISES = [
    ex("Barbell Curl", BP.BICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Classic bicep exercise using a straight barbell.",
       ["Keep elbows pinned to sides", "Full extension at the bottom", "Squeeze at the top", "Don't swing"]),
    ex("Dumbbell Curl", BP.BICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Unilateral bicep curl allowing supination throughout the movement.",
       ["Supinate the wrist as you curl", "Control the negative", "Don't use momentum"]),
    ex("Hammer Curl", BP.BICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Neutral-grip curl targeting the brachialis and brachioradialis alongside the biceps.",
       ["Keep palms facing each other", "Curl to shoulder height", "Keep elbows stationary"]),
    ex("Preacher Curl", BP.BICEPS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Curl performed on a preacher bench to isolate the biceps and eliminate cheating.",
       ["Keep upper arms flat on the pad", "Full extension at the bottom", "Squeeze at the top"]),
    ex("Concentration Curl", BP.BICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Seated single-arm curl with the elbow braced against the inner thigh.",
       ["Brace elbow against inner thigh", "Curl slowly", "Squeeze at the top"]),
    ex("Cable Curl", BP.BICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Bicep curl using a cable for constant tension.",
       ["Stand facing the cable", "Keep elbows at sides", "Squeeze at the top"]),
    ex("Incline Dumbbell Curl", BP.BICEPS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Curl on an incline bench for a greater stretch on the long head of the biceps.",
       ["Set bench to 45 degrees", "Let arms hang straight down", "Curl without moving the upper arm"]),
    ex("Spider Curl", BP.BICEPS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Curl performed face-down on an incline bench for peak contraction emphasis.",
       ["Lie face down on incline bench", "Let arms hang vertical", "Curl and squeeze hard at the top"]),
]

TRICEPS_EXERCISES = [
    ex("Close-Grip Bench Press", BP.TRICEPS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Bench press with a narrow grip emphasizing the triceps.",
       ["Hands shoulder-width apart", "Keep elbows close to body", "Lower bar to lower chest"]),
    ex("Tricep Pushdown", BP.TRICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Cable exercise pushing a bar or rope downward to extend the arms.",
       ["Keep elbows pinned to sides", "Full lockout at the bottom", "Control the return"]),
    ex("Overhead Tricep Extension", BP.TRICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Dumbbell or cable extension performed overhead to target the long head.",
       ["Keep elbows close to head", "Lower weight behind head", "Full extension at the top"]),
    ex("Skull Crusher", BP.TRICEPS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Lying tricep extension lowering the bar toward the forehead.",
       ["Keep upper arms vertical", "Lower to forehead or just behind", "Don't flare elbows"]),
    ex("Tricep Dip", BP.TRICEPS, ADV.INTERMEDIATE, CAT.CALISTHENICS,
       "Dip variation with an upright torso emphasizing the triceps.",
       ["Keep body vertical", "Lower until upper arms are parallel", "Full lockout at the top"]),
    ex("Tricep Kickback", BP.TRICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Bent-over dumbbell extension isolating the triceps.",
       ["Keep upper arm parallel to floor", "Extend fully", "Squeeze at the top"]),
    ex("Rope Pushdown", BP.TRICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Cable pushdown using a rope attachment, allowing wrists to spread at the bottom.",
       ["Pull rope apart at the bottom", "Keep elbows at sides", "Squeeze the contraction"]),
]

FOREARM_EXERCISES = [
    ex("Wrist Curl", BP.FOREARMS, ADV.BEGINNER, CAT.STRENGTH,
       "Isolation exercise for the wrist flexors performed seated.",
       ["Rest forearms on thighs", "Curl wrists upward", "Control the descent"]),
    ex("Reverse Wrist Curl", BP.FOREARMS, ADV.BEGINNER, CAT.STRENGTH,
       "Isolation exercise for the wrist extensors.",
       ["Rest forearms on thighs, palms down", "Extend wrists upward", "Use light weight"]),
    ex("Farmer's Walk", BP.FOREARMS, ADV.BEGINNER, CAT.STRENGTH,
       "Loaded carry exercise building grip strength and overall conditioning.",
       ["Hold heavy dumbbells at sides", "Walk with upright posture", "Keep shoulders packed"]),
    ex("Dead Hang", BP.FOREARMS, ADV.BEGINNER, CAT.CALISTHENICS,
       "Hanging from a pull-up bar to improve grip strength and decompress the spine.",
       ["Full grip on the bar", "Relax shoulders slightly", "Breathe steadily"]),
]

ABS_EXERCISES = [
    ex("Crunch", BP.ABS, ADV.BEGINNER, CAT.CALISTHENICS,
       "Basic abdominal exercise curling the torso toward the knees.",
       ["Don't pull on neck", "Focus on contracting abs", "Exhale on the way up"]),
    ex("Plank", BP.ABS, ADV.BEGINNER, CAT.CALISTHENICS,
       "Isometric core exercise maintaining a rigid body position.",
       ["Keep body in a straight line", "Engage glutes and abs", "Don't let hips sag"]),
    ex("Hanging Leg Raise", BP.ABS, ADV.INTERMEDIATE, CAT.CALISTHENICS,
       "Hanging exercise raising the legs to work the lower abs.",
       ["Hang from a bar with straight arms", "Raise legs to 90 degrees", "Control the descent", "Avoid swinging"]),
    ex("Ab Wheel Rollout", BP.ABS, ADV.ADVANCED, CAT.CALISTHENICS,
       "Core exercise using an ab wheel, rolling out from a kneeling position.",
       ["Start on knees", "Roll out slowly", "Keep core extremely tight", "Don't let hips sag"]),
    ex("Cable Crunch", BP.ABS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Weighted crunch using a cable machine for progressive overload on abs.",
       ["Kneel in front of cable", "Crunch downward", "Focus on flexing the spine"]),
    ex("Sit-Up", BP.ABS, ADV.BEGINNER, CAT.CALISTHENICS,
       "Full-range abdominal exercise going from lying flat to upright.",
       ["Anchor feet if needed", "Come all the way up", "Control the descent"]),
    ex("Mountain Climber", BP.ABS, ADV.BEGINNER, CAT.HIIT,
       "Dynamic core exercise alternating knees toward chest in a plank position.",
       ["Maintain plank position", "Drive knees toward chest rapidly", "Keep hips level"]),
    ex("Dead Bug", BP.ABS, ADV.BEGINNER, CAT.CALISTHENICS,
       "Supine core exercise extending opposite arm and leg while maintaining lower back contact.",
       ["Press lower back into floor", "Extend opposite arm and leg", "Move slowly and controlled"]),
    ex("L-Sit", BP.ABS, ADV.ADVANCED, CAT.CALISTHENICS,
       "Isometric hold with legs extended horizontally while supported on hands or parallettes.",
       ["Press down through hands", "Keep legs straight and horizontal", "Engage hip flexors and abs"]),
    ex("Toes to Bar", BP.ABS, ADV.ADVANCED, CAT.CALISTHENICS,
       "Hanging exercise bringing toes up to touch the pull-up bar.",
       ["Use a kip if needed", "Bring toes all the way to bar", "Control the descent"]),
]

OBLIQUE_EXERCISES = [
    ex("Russian Twist", BP.OBLIQUES, ADV.BEGINNER, CAT.CALISTHENICS,
       "Rotational core exercise performed seated with feet elevated.",
       ["Lean back slightly", "Rotate torso side to side", "Keep feet off the ground"]),
    ex("Side Plank", BP.OBLIQUES, ADV.BEGINNER, CAT.CALISTHENICS,
       "Isometric lateral core exercise holding a sideways plank.",
       ["Stack feet or stagger them", "Keep body in a straight line", "Don't let hip drop"]),
    ex("Woodchopper", BP.OBLIQUES, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Cable or dumbbell rotational exercise mimicking a wood-chopping motion.",
       ["Rotate through the torso", "Keep arms extended", "Control the motion"]),
    ex("Bicycle Crunch", BP.OBLIQUES, ADV.BEGINNER, CAT.CALISTHENICS,
       "Dynamic crunch alternating elbow to opposite knee.",
       ["Bring elbow to opposite knee", "Fully extend the other leg", "Don't pull on neck"]),
]

QUADRICEPS_EXERCISES = [
    ex("Barbell Back Squat", BP.QUADRICEPS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "King of all exercises — compound movement targeting quads, glutes, and core.",
       ["Bar on upper traps", "Break at hips and knees together", "Depth to at least parallel", "Drive through the whole foot"]),
    ex("Front Squat", BP.QUADRICEPS, ADV.ADVANCED, CAT.STRENGTH,
       "Squat variation with the bar in front, emphasizing quads and core.",
       ["Elbows high, bar on front delts", "Stay upright", "Depth to parallel or below"]),
    ex("Goblet Squat", BP.QUADRICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Dumbbell or kettlebell squat holding the weight at chest level.",
       ["Hold weight at chest", "Push knees out", "Keep torso upright"]),
    ex("Leg Press", BP.QUADRICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Machine-based compound pressing movement for the legs.",
       ["Place feet shoulder-width apart", "Lower until knees are at 90 degrees", "Don't lock out knees fully"]),
    ex("Leg Extension", BP.QUADRICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Machine isolation exercise for the quadriceps.",
       ["Adjust pad to sit above ankles", "Extend fully", "Squeeze at the top", "Control the descent"]),
    ex("Bulgarian Split Squat", BP.QUADRICEPS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Single-leg squat with the rear foot elevated on a bench.",
       ["Rear foot on bench", "Lower until front thigh is parallel", "Keep torso upright"]),
    ex("Walking Lunge", BP.QUADRICEPS, ADV.BEGINNER, CAT.STRENGTH,
       "Dynamic lunge stepping forward alternately with each leg.",
       ["Take long steps", "Lower until both knees are at 90 degrees", "Keep torso upright"]),
    ex("Hack Squat", BP.QUADRICEPS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Machine squat emphasizing the quadriceps with back support.",
       ["Place feet low on platform for quad focus", "Lower to at least 90 degrees", "Drive through feet"]),
    ex("Pistol Squat", BP.QUADRICEPS, ADV.EXPERT, CAT.CALISTHENICS,
       "Single-leg squat performed with the other leg extended in front.",
       ["Extend non-working leg forward", "Squat all the way down on one leg", "Arms forward for balance"]),
    ex("Wall Sit", BP.QUADRICEPS, ADV.BEGINNER, CAT.CALISTHENICS,
       "Isometric exercise holding a sitting position against a wall.",
       ["Back flat against wall", "Thighs parallel to floor", "Hold the position"]),
]

HAMSTRING_EXERCISES = [
    ex("Romanian Deadlift", BP.HAMSTRINGS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Hip-hinge movement emphasizing the hamstrings and glutes.",
       ["Keep bar close to legs", "Hinge at hips with slight knee bend", "Feel the stretch in hamstrings", "Squeeze glutes at the top"]),
    ex("Lying Leg Curl", BP.HAMSTRINGS, ADV.BEGINNER, CAT.STRENGTH,
       "Machine isolation exercise for the hamstrings performed face down.",
       ["Lie face down on machine", "Curl weight toward glutes", "Control the descent"]),
    ex("Seated Leg Curl", BP.HAMSTRINGS, ADV.BEGINNER, CAT.STRENGTH,
       "Machine isolation exercise for the hamstrings performed seated.",
       ["Adjust pad above heels", "Curl weight under the seat", "Squeeze at full contraction"]),
    ex("Stiff-Leg Deadlift", BP.HAMSTRINGS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Deadlift variation with minimal knee bend for maximum hamstring stretch.",
       ["Keep legs nearly straight", "Lower bar along the legs", "Feel the stretch", "Don't round the back"]),
    ex("Good Morning", BP.HAMSTRINGS, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Barbell exercise hinging at hips with the bar on the back.",
       ["Bar on upper back like a squat", "Hinge forward keeping back straight", "Return to standing by squeezing glutes"]),
    ex("Nordic Hamstring Curl", BP.HAMSTRINGS, ADV.ADVANCED, CAT.CALISTHENICS,
       "Eccentric-focused bodyweight exercise for hamstring strength.",
       ["Kneel with feet anchored", "Lower body forward slowly", "Catch yourself and push back up"]),
    ex("Glute-Ham Raise", BP.HAMSTRINGS, ADV.ADVANCED, CAT.STRENGTH,
       "Posterior chain exercise performed on a GHD machine.",
       ["Start with torso parallel to floor", "Curl up using hamstrings", "Squeeze glutes at the top"]),
]

GLUTE_EXERCISES = [
    ex("Hip Thrust", BP.GLUTES, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Barbell hip extension targeting the glutes maximally.",
       ["Upper back on bench", "Bar over hip crease", "Drive hips to full extension", "Squeeze glutes at the top"]),
    ex("Glute Bridge", BP.GLUTES, ADV.BEGINNER, CAT.STRENGTH,
       "Bodyweight or loaded hip extension performed on the floor.",
       ["Lie on back with knees bent", "Drive hips up", "Squeeze glutes at the top"]),
    ex("Cable Pull-Through", BP.GLUTES, ADV.BEGINNER, CAT.STRENGTH,
       "Cable hip hinge exercise for glutes and hamstrings.",
       ["Face away from cable", "Hinge at hips", "Squeeze glutes to stand up"]),
    ex("Donkey Kick", BP.GLUTES, ADV.BEGINNER, CAT.CALISTHENICS,
       "Kneeling glute isolation exercise kicking one leg back.",
       ["Start on all fours", "Kick one leg back and up", "Squeeze glute at the top"]),
    ex("Step-Up", BP.GLUTES, ADV.BEGINNER, CAT.STRENGTH,
       "Unilateral exercise stepping onto a raised platform.",
       ["Step onto box with full foot", "Drive through the heel", "Control the step down"]),
    ex("Sumo Squat", BP.GLUTES, ADV.BEGINNER, CAT.STRENGTH,
       "Wide-stance squat emphasizing glutes and inner thighs.",
       ["Wide stance with toes pointed out", "Lower until thighs are parallel", "Push knees out"]),
]

CALF_EXERCISES = [
    ex("Standing Calf Raise", BP.CALVES, ADV.BEGINNER, CAT.STRENGTH,
       "Calf exercise performed standing on a platform or machine.",
       ["Full range of motion", "Pause at the top", "Stretch at the bottom"]),
    ex("Seated Calf Raise", BP.CALVES, ADV.BEGINNER, CAT.STRENGTH,
       "Calf exercise performed seated, targeting the soleus muscle.",
       ["Place pad on lower thighs", "Push up on toes", "Stretch at the bottom"]),
    ex("Donkey Calf Raise", BP.CALVES, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Calf raise performed bent over with weight on the hips.",
       ["Bend at hips with back flat", "Raise up on toes", "Full stretch at the bottom"]),
    ex("Single-Leg Calf Raise", BP.CALVES, ADV.INTERMEDIATE, CAT.CALISTHENICS,
       "Unilateral calf raise for balanced development.",
       ["Hold onto something for balance", "Full range of motion", "Pause at the top"]),
]

FULL_BODY_EXERCISES = [
    ex("Barbell Clean and Press", BP.FULL_BODY, ADV.ADVANCED, CAT.OLYMPIC_LIFTING,
       "Olympic lift cleaning the bar to shoulders then pressing overhead.",
       ["Start with bar on floor", "Explosive hip extension", "Catch at shoulders", "Press overhead"]),
    ex("Power Clean", BP.FULL_BODY, ADV.ADVANCED, CAT.OLYMPIC_LIFTING,
       "Explosive Olympic lift bringing the bar from floor to shoulder position.",
       ["Start in deadlift position", "Explosive triple extension", "Catch in front rack position"]),
    ex("Snatch", BP.FULL_BODY, ADV.EXPERT, CAT.OLYMPIC_LIFTING,
       "Olympic lift bringing the bar from floor to overhead in one motion.",
       ["Wide grip", "Explosive pull", "Catch overhead with locked arms", "Stand up from squat"]),
    ex("Thruster", BP.FULL_BODY, ADV.INTERMEDIATE, CAT.STRENGTH,
       "Front squat into overhead press in one fluid motion.",
       ["Start in front rack position", "Squat to depth", "Drive up and press overhead", "Use leg drive"]),
    ex("Kettlebell Swing", BP.FULL_BODY, ADV.BEGINNER, CAT.STRENGTH,
       "Explosive hip hinge swinging a kettlebell to shoulder height.",
       ["Hinge at hips", "Explosive hip drive", "Arms guide the bell, don't lift", "Squeeze glutes at top"]),
    ex("Turkish Get-Up", BP.FULL_BODY, ADV.ADVANCED, CAT.STRENGTH,
       "Complex floor-to-standing movement holding a weight overhead.",
       ["Keep arm locked out overhead", "Move through each position deliberately", "Eyes on the weight"]),
    ex("Man Maker", BP.FULL_BODY, ADV.ADVANCED, CAT.HIIT,
       "Combination of push-up, renegade row, squat clean, and overhead press.",
       ["Start in push-up position with dumbbells", "Push-up, row each side", "Jump feet to hands", "Clean and press"]),
    ex("Burpee", BP.FULL_BODY, ADV.BEGINNER, CAT.HIIT,
       "High-intensity bodyweight exercise combining a squat thrust with a jump.",
       ["Drop to push-up position", "Perform a push-up", "Jump feet to hands", "Jump up with arms overhead"]),
    ex("Battle Rope Slam", BP.FULL_BODY, ADV.BEGINNER, CAT.HIIT,
       "Explosive conditioning exercise slamming heavy ropes.",
       ["Grip ropes at ends", "Raise arms overhead", "Slam ropes down forcefully", "Maintain athletic stance"]),
]

CARDIO_EXERCISES = [
    ex("Running", BP.CARDIO, ADV.BEGINNER, CAT.CARDIO,
       "Steady-state or interval running for cardiovascular fitness.",
       ["Maintain upright posture", "Land midfoot", "Keep a consistent pace", "Breathe rhythmically"]),
    ex("Cycling", BP.CARDIO, ADV.BEGINNER, CAT.CARDIO,
       "Stationary or outdoor cycling for cardiovascular endurance.",
       ["Adjust seat height properly", "Maintain cadence of 60-100 RPM", "Keep upper body relaxed"]),
    ex("Rowing Machine", BP.CARDIO, ADV.BEGINNER, CAT.CARDIO,
       "Full-body cardio using a rowing ergometer.",
       ["Drive with legs first", "Follow with back lean and arm pull", "Return in reverse order", "Keep core engaged"]),
    ex("Jump Rope", BP.CARDIO, ADV.BEGINNER, CAT.CARDIO,
       "Classic cardio exercise improving coordination and endurance.",
       ["Stay on balls of feet", "Small jumps", "Turn rope with wrists not arms", "Keep elbows close to body"]),
    ex("Stair Climber", BP.CARDIO, ADV.BEGINNER, CAT.CARDIO,
       "Machine-based cardio simulating stair climbing.",
       ["Stand upright", "Don't lean on the handles", "Maintain a steady pace"]),
    ex("Swimming", BP.CARDIO, ADV.BEGINNER, CAT.CARDIO,
       "Low-impact full-body cardio performed in water.",
       ["Streamline your body", "Breathe bilaterally", "Maintain a consistent stroke"]),
    ex("Elliptical Trainer", BP.CARDIO, ADV.BEGINNER, CAT.CARDIO,
       "Low-impact cardio machine mimicking running without joint stress.",
       ["Stand upright", "Use arms for full-body engagement", "Maintain a steady stride"]),
    ex("Box Jump", BP.CARDIO, ADV.INTERMEDIATE, CAT.PLYOMETRIC,
       "Explosive plyometric exercise jumping onto an elevated box.",
       ["Start in an athletic stance", "Swing arms for momentum", "Land softly with both feet", "Step down, don't jump down"]),
    ex("Jumping Jack", BP.CARDIO, ADV.BEGINNER, CAT.CARDIO,
       "Classic calisthenic exercise for warming up and cardio.",
       ["Start with feet together", "Jump feet out while raising arms", "Return to starting position"]),
    ex("High Knees", BP.CARDIO, ADV.BEGINNER, CAT.HIIT,
       "Running in place bringing knees to hip height.",
       ["Drive knees up to hip level", "Pump arms", "Stay on balls of feet", "Keep a fast pace"]),
    ex("Sprint Intervals", BP.CARDIO, ADV.INTERMEDIATE, CAT.HIIT,
       "Short all-out sprints followed by rest periods.",
       ["Sprint for 20-30 seconds", "Rest for 60-90 seconds", "Maintain form even when tired"]),
    ex("Sled Push", BP.CARDIO, ADV.INTERMEDIATE, CAT.HIIT,
       "Pushing a weighted sled for conditioning and leg power.",
       ["Keep arms extended", "Drive through the legs", "Maintain a forward lean"]),
]

FLEXIBILITY_EXERCISES = [
    ex("Downward Dog", BP.FULL_BODY, ADV.BEGINNER, CAT.YOGA,
       "Yoga pose stretching the hamstrings, calves, shoulders, and spine.",
       ["Hands shoulder-width apart", "Push hips up and back", "Press heels toward floor", "Keep back straight"]),
    ex("Warrior II Pose", BP.FULL_BODY, ADV.BEGINNER, CAT.YOGA,
       "Yoga standing pose building strength and flexibility.",
       ["Front knee over ankle", "Arms extended parallel to floor", "Gaze over front hand"]),
    ex("Child's Pose", BP.FULL_BODY, ADV.BEGINNER, CAT.YOGA,
       "Gentle resting yoga pose stretching the back and hips.",
       ["Knees wide, big toes together", "Reach arms forward", "Relax forehead to floor"]),
    ex("Pigeon Pose", BP.GLUTES, ADV.INTERMEDIATE, CAT.YOGA,
       "Deep hip-opening yoga pose stretching the glutes and hip flexors.",
       ["Front shin angled across the mat", "Square hips forward", "Lower torso over front leg"]),
    ex("Cat-Cow Stretch", BP.BACK, ADV.BEGINNER, CAT.STRETCHING,
       "Spinal mobility exercise alternating between arched and rounded back positions.",
       ["Start on all fours", "Inhale, arch back and look up (cow)", "Exhale, round back and tuck chin (cat)"]),
    ex("Standing Hamstring Stretch", BP.HAMSTRINGS, ADV.BEGINNER, CAT.STRETCHING,
       "Standing stretch for the hamstrings with one leg elevated.",
       ["Place heel on elevated surface", "Keep leg straight", "Hinge forward at hips", "Hold 20-30 seconds"]),
    ex("Hip Flexor Stretch", BP.QUADRICEPS, ADV.BEGINNER, CAT.STRETCHING,
       "Kneeling or standing stretch for the hip flexors.",
       ["Kneel on one knee", "Push hips forward", "Keep torso upright", "Hold 20-30 seconds"]),
    ex("World's Greatest Stretch", BP.FULL_BODY, ADV.INTERMEDIATE, CAT.STRETCHING,
       "Dynamic multi-joint stretch targeting hips, thoracic spine, and hamstrings.",
       ["Lunge forward", "Place opposite hand on floor", "Rotate torso and reach up", "Hold briefly then switch"]),
    ex("Foam Rolling IT Band", BP.QUADRICEPS, ADV.BEGINNER, CAT.STRETCHING,
       "Self-myofascial release for the iliotibial band using a foam roller.",
       ["Lie on side with roller under outer thigh", "Roll from hip to knee", "Pause on tender spots"]),
    ex("Couch Stretch", BP.QUADRICEPS, ADV.INTERMEDIATE, CAT.STRETCHING,
       "Deep hip flexor and quad stretch using a wall or couch.",
       ["Place rear foot against wall", "Front foot in lunge position", "Push hips forward", "Keep torso upright"]),
]


# ---------------------------------------------------------------------------
# Combine all categories
# ---------------------------------------------------------------------------
ALL_EXERCISES = (
    CHEST_EXERCISES
    + BACK_EXERCISES
    + SHOULDER_EXERCISES
    + BICEPS_EXERCISES
    + TRICEPS_EXERCISES
    + FOREARM_EXERCISES
    + ABS_EXERCISES
    + OBLIQUE_EXERCISES
    + QUADRICEPS_EXERCISES
    + HAMSTRING_EXERCISES
    + GLUTE_EXERCISES
    + CALF_EXERCISES
    + FULL_BODY_EXERCISES
    + CARDIO_EXERCISES
    + FLEXIBILITY_EXERCISES
)


# ---------------------------------------------------------------------------
# Init helpers
# ---------------------------------------------------------------------------
def build_exercise(name, body_part, advancement, category, description, hints):
    """Build an Exercise Pydantic model with a deterministic _id."""
    now = datetime.utcnow()
    return Exercise(
        id=make_exercise_id(name),
        name=name,
        body_part=body_part,
        advancement=advancement,
        category=category,
        description=description,
        hints=hints,
        image=None,
        video_url=None,
        created_at=now,
        updated_at=now,
    )


async def init_exercises():
    """Seed the exercises collection (idempotent — skips if data exists)."""
    try:
        print("Connecting to MongoDB…")
        await connect_to_mongodb()

        db = get_database()
        collection = db[settings.EXERCISES_COLLECTION]

        existing_count = await collection.count_documents({})
        if existing_count > 0:
            print(f"⚠️  Collection already has {existing_count} exercises — skipping.")
            return

        docs = []
        for row in ALL_EXERCISES:
            exercise = build_exercise(*row)
            docs.append(exercise.model_dump(by_alias=True))

        result = await collection.insert_many(docs)

        print(f"✅ Inserted {len(result.inserted_ids)} exercises.")
        print(f"   Categories: Chest({len(CHEST_EXERCISES)}), Back({len(BACK_EXERCISES)}), "
              f"Shoulders({len(SHOULDER_EXERCISES)}), Biceps({len(BICEPS_EXERCISES)}), "
              f"Triceps({len(TRICEPS_EXERCISES)}), Forearms({len(FOREARM_EXERCISES)}), "
              f"Abs({len(ABS_EXERCISES)}), Obliques({len(OBLIQUE_EXERCISES)}), "
              f"Quads({len(QUADRICEPS_EXERCISES)}), Hamstrings({len(HAMSTRING_EXERCISES)}), "
              f"Glutes({len(GLUTE_EXERCISES)}), Calves({len(CALF_EXERCISES)}), "
              f"Full Body({len(FULL_BODY_EXERCISES)}), Cardio({len(CARDIO_EXERCISES)}), "
              f"Flexibility({len(FLEXIBILITY_EXERCISES)})")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await disconnect_from_mongodb()


if __name__ == "__main__":
    print(f"Total exercises to seed: {len(ALL_EXERCISES)}")
    asyncio.run(init_exercises())
