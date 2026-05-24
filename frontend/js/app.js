document.addEventListener('DOMContentLoaded', () => {
    // API URL configuration
    const API_BASE = window.location.origin;

    // Elements
    const form = document.getElementById('prediction-form');
    const battingSelect = document.getElementById('batting_team');
    const bowlingSelect = document.getElementById('bowling_team');
    const venueSelect = document.getElementById('venue');
    const currentScoreInput = document.getElementById('current_score');
    const wicketsSelect = document.getElementById('wickets');
    const oversInput = document.getElementById('overs');
    const runsLast5Input = document.getElementById('runs_in_last_5');
    const wicketsLast5Select = document.getElementById('wickets_in_last_5');

    const resultsPlaceholder = document.getElementById('results-placeholder');
    const resultsLoading = document.getElementById('results-loading');
    const resultsContainer = document.getElementById('results-container');

    const predictedRangeText = document.getElementById('predicted-score-range');
    const mostProbableText = document.getElementById('most-probable-score');
    const meterFillBar = document.getElementById('meter-fill-bar');
    const meterMarkerPin = document.getElementById('meter-marker-pin');
    const markerTooltipVal = document.getElementById('marker-tooltip-val');

    const currentRRText = document.getElementById('current-rr');
    const predictedRPOText = document.getElementById('predicted-rpo');
    const linearProjText = document.getElementById('linear-proj');

    // Load teams and venues metadata on page load
    async function loadMetadata() {
        try {
            const response = await fetch(`${API_BASE}/api/meta`);
            if (!response.ok) throw new Error("Failed to load metadata");
            
            const data = await response.json();
            
            // Populate Batting Team
            data.teams.forEach(team => {
                const opt1 = document.createElement('option');
                opt1.value = team;
                opt1.textContent = team;
                battingSelect.appendChild(opt1);

                const opt2 = document.createElement('option');
                opt2.value = team;
                opt2.textContent = team;
                bowlingSelect.appendChild(opt2);
            });

            // Populate Venues
            data.venues.forEach(venue => {
                const opt = document.createElement('option');
                opt.value = venue;
                opt.textContent = venue;
                venueSelect.appendChild(opt);
            });
        } catch (error) {
            console.error("Metadata load error:", error);
            alert("Could not connect to the backend server. Please make sure the FastAPI server is running.");
        }
    }

    // Custom cricket overs validation: e.g. 10.6 is invalid (overs can only end in .0 to .5)
    function validateOvers(oversVal) {
        const decimalPart = Math.round((oversVal % 1) * 10);
        if (decimalPart > 5) {
            return false;
        }
        return true;
    }

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const battingTeam = battingSelect.value;
        const bowlingTeam = bowlingSelect.value;
        const venue = venueSelect.value;
        const currentScore = parseInt(currentScoreInput.value);
        const wickets = parseInt(wicketsSelect.value);
        const overs = parseFloat(oversInput.value);
        const runsInLast5 = parseInt(runsLast5Input.value);
        const wicketsInLast5 = parseInt(wicketsLast5Select.value);

        // Validation Checks
        if (battingTeam === bowlingTeam) {
            alert("Error: Batting team and Bowling team cannot be the same.");
            return;
        }

        if (!validateOvers(overs)) {
            alert("Error: Overs completed must end between .0 and .5 (e.g. 10.4 represents 10 overs and 4 balls). Values like 10.6 are invalid.");
            return;
        }

        if (currentScore < runsInLast5) {
            alert("Error: Current score cannot be less than runs scored in the last 5 overs.");
            return;
        }

        if (wickets < wicketsInLast5) {
            alert("Error: Wickets lost cannot be less than wickets lost in the last 5 overs.");
            return;
        }

        // Show loading state
        resultsPlaceholder.classList.add('hidden');
        resultsContainer.classList.add('hidden');
        resultsLoading.classList.remove('hidden');

        try {
            const response = await fetch(`${API_BASE}/api/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    batting_team: battingTeam,
                    bowling_team: bowlingTeam,
                    venue: venue,
                    current_score: currentScore,
                    wickets: wickets,
                    overs: overs,
                    runs_in_last_5: runsInLast5,
                    wickets_in_last_5: wicketsInLast5
                })
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Prediction failed");
            }

            const result = await response.json();

            // Populate prediction results
            predictedRangeText.textContent = `${result.min_predicted_score} - ${result.max_predicted_score}`;
            mostProbableText.textContent = result.predicted_score;

            // Calculate current run rate
            // To be accurate, convert overs to balls (e.g. 10.3 overs = 10 * 6 + 3 = 63 balls)
            const completedOversInt = Math.floor(overs);
            const extraBalls = Math.round((overs % 1) * 10);
            const totalBalls = (completedOversInt * 6) + extraBalls;
            
            const currentRRate = totalBalls > 0 ? (currentScore / (totalBalls / 6)) : 0.0;
            currentRRText.textContent = currentRRate.toFixed(2);
            
            predictedRPOText.textContent = result.predicted_rpo_remaining.toFixed(2);
            
            // Linear projection based on current run rate
            const linearProj = Math.round(currentRRate * 20);
            linearProjText.textContent = linearProj;

            // Update Progress Meter
            // Map predicted score between 100 and 250 runs
            const minMeter = 100;
            const maxMeter = 250;
            const percentage = Math.max(0, Math.min(100, ((result.predicted_score - minMeter) / (maxMeter - minMeter)) * 100));
            
            meterFillBar.style.width = `${percentage}%`;
            meterMarkerPin.style.left = `${percentage}%`;
            markerTooltipVal.textContent = result.predicted_score;

            // Transition states
            resultsLoading.classList.add('hidden');
            resultsContainer.classList.remove('hidden');

        } catch (error) {
            console.error("Prediction error:", error);
            alert(`Error: ${error.message}`);
            resultsLoading.classList.add('hidden');
            resultsPlaceholder.classList.remove('hidden');
        }
    });

    // Initialize
    loadMetadata();
});
