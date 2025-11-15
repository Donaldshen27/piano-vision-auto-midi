import numpy as np
from sklearn.cluster import KMeans
from pretty_midi import PrettyMIDI, Instrument, Note
from collections import defaultdict

def assign_notes_to_hands(midi_data, max_fingers=5, allowed_spread=8):
    """
    Splits the MIDI notes into two clusters (left and right) using KMeans clustering,
    and then refines the assignment so that each hand is assigned notes using at most
    max_fingers distinct finger numbers and within a pitch range not exceeding allowed_spread semitones.
    This simulates a small hand that can only cover an 8-semitone span on the keyboard.

    Parameters:
      midi_data: the PrettyMIDI object loaded from a MIDI file.
      max_fingers: maximum distinct finger numbers allowed per hand (default 5).
      allowed_spread: maximum allowed pitch range (in semitones) for each hand (default 8).

    Returns:
      A tuple (left_hand_notes, right_hand_notes) where each element is a list
      of tuples representing (pitch, start, end, velocity).
    """
    # Extract note information from MIDI data.
    notes = []
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            notes.append((note.pitch, note.start, note.end, note.velocity))
    
    # Sort notes by start time and pitch
    notes.sort(key=lambda x: (x[1], x[0]))
    
    left_hand = []
    right_hand = []
    active_notes = {'left': [], 'right': []}
    
    for note in notes:
        pitch, start, end, velocity = note
        
        # Calculate current hand states
        hand_states = {}
        for hand in ['left', 'right']:
            active_notes[hand] = [n for n in active_notes[hand] if n[3] > start]
            current_pitches = [n[0] for n in active_notes[hand]]
            
            # Calculate finger usage based on chromatic scale positions
            finger_positions = {p % 12 for p in current_pitches}  # More natural finger spread
            min_pitch = min(current_pitches) if current_pitches else pitch
            max_pitch = max(current_pitches) if current_pitches else pitch
            
            hand_states[hand] = {
                'fingers_used': len(finger_positions),
                'spread': max_pitch - min_pitch if current_pitches else 0,
                'min_pitch': min_pitch,
                'max_pitch': max_pitch
            }
        
        # Calculate assignment costs with weighted factors
        costs = {}
        for hand in ['left', 'right']:
            state = hand_states[hand]
            current_span = state['max_pitch'] - state['min_pitch'] if current_pitches else 0
            
            # Proposed new span if we add this note
            new_min = min(state['min_pitch'], pitch) if current_pitches else pitch
            new_max = max(state['max_pitch'], pitch) if current_pitches else pitch
            new_span = new_max - new_min
            
            # Cost components (weights can be adjusted)
            span_cost = max(0, new_span - allowed_spread) ** 2  # Quadratic penalty
            finger_cost = 2.0 if (state['fingers_used'] >= max_fingers and 
                                (pitch % 12) not in {p % 12 for p in current_pitches}) else 0
            register_cost = 0.8 if (hand == 'left' and pitch >= 60) or (hand == 'right' and pitch < 60) else 0
            density_cost = 0.2 * len(current_pitches)  # Prefer less crowded hand
            
            costs[hand] = span_cost + finger_cost + register_cost + density_cost
        
        # Assign with hysteresis to prevent hand oscillation
        if costs['left'] < costs['right'] * 0.9:  # 10% preference threshold
            left_hand.append(note)
            active_notes['left'].append(note)
        elif costs['right'] < costs['left'] * 0.9:
            right_hand.append(note)
            active_notes['right'].append(note)
        else:
            # Maintain current hand preference for similar costs
            if len(left_hand) > len(right_hand):
                right_hand.append(note)
                active_notes['right'].append(note)
            else:
                left_hand.append(note)
                active_notes['left'].append(note)
    
    return left_hand, right_hand

def dynamic_programming_assign_hands(midi_data, max_fingers=5, allowed_spread=8):
    """
    Assigns MIDI notes to left and right hands using dynamic programming to minimize a cost function
    that considers hand span, finger usage, and register preference.

    Parameters:
      midi_data: the PrettyMIDI object loaded from a MIDI file.
      max_fingers: maximum distinct finger numbers allowed per hand (default 5).
      allowed_spread: maximum allowed pitch range (in semitones) for each hand (default 8).

    Returns:
      A tuple (left_hand_notes, right_hand_notes) where each element is a list
      of tuples representing (pitch, start, end, velocity).
    """
    # Extract note information from MIDI data and sort.
    notes = []
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            notes.append((note.pitch, note.start, note.end, note.velocity))
    notes.sort(key=lambda x: (x[1], x[0])) # Sort by start time, then pitch

    n_notes = len(notes)
    if n_notes == 0:
        return [], []

    # Initialize DP table: dp[i][hand] = minimum cost to assign notes up to index i,
    # ending with note i assigned to 'hand' ('left' or 'right').
    dp = defaultdict(lambda: {'left': float('inf'), 'right': float('inf')})
    dp[-1] = {'left': 0, 'right': 0} # Base case: cost before any notes is 0

    hand_assignment = {} # Store hand assignment decisions for backtracking

    for i in range(n_notes):
        current_note = notes[i]

        for hand in ['left', 'right']:
            # Calculate cost of assigning current_note to 'hand'
            cost_to_assign_hand = calculate_cost(current_note, hand, hand_assignment, notes[:i], max_fingers, allowed_spread)

            for prev_hand in ['left', 'right']:
                # Transition from previous assignment (prev_hand) to current assignment (hand)
                prev_cost = dp[i-1][prev_hand]
                current_total_cost = prev_cost + cost_to_assign_hand

                if current_total_cost < dp[i][hand]:
                    dp[i][hand] = current_total_cost
                    hand_assignment[i, hand] = prev_hand # Store the preceding hand for backtracking

    # Backtrack to find the optimal hand assignments
    final_hand_assignments = {}
    if dp[n_notes-1]['left'] <= dp[n_notes-1]['right']:
        final_hand = 'left'
    else:
        final_hand = 'right'

    final_cost = min(dp[n_notes-1]['left'], dp[n_notes-1]['right'])
    final_hand_assignments[n_notes-1] = final_hand

    for i in range(n_notes - 2, -1, -1):
        final_hand = hand_assignment[i+1, final_hand] # Get the hand assignment that led to the min cost for the next note
        final_hand_assignments[i] = final_hand

    left_hand_notes = []
    right_hand_notes = []
    for i in range(n_notes):
        note = notes[i]
        if final_hand_assignments[i] == 'left':
            left_hand_notes.append(note)
        else:
            right_hand_notes.append(note)

    return left_hand_notes, right_hand_notes

def calculate_cost(note, hand, current_assignments, previous_notes, max_fingers, allowed_spread):
    """
    Calculates the cost of assigning a note to a hand, considering finger usage, spread, and register.

    Parameters:
      note: The note (pitch, start, end, velocity) to be assigned.
      hand: 'left' or 'right' hand.
      current_assignments: Dictionary with keys as (note_index, hand) for notes already assigned.
      previous_notes: List of notes already processed (up to the current note's index - 1).
      max_fingers: Maximum fingers allowed per hand.
      allowed_spread: Maximum allowed pitch spread for a hand.

    Returns:
      The cost of assigning the note to the hand.
    """
    pitch, start, end, velocity = note

    active_notes_pitch = []
    assigned_hand_notes = []

    # Only consider assignments for notes that actually exist in previous_notes.
    for (n_idx, hand_assigned), prev in current_assignments.items():
        if n_idx >= len(previous_notes):
            # Skip any entries with indices not in the current previous_notes context.
            continue
        if hand_assigned == hand:
            assigned_note = previous_notes[n_idx]  # Use the integer note index directly.
            if assigned_note[2] > start:  # if note end time is after current note start time, it's active.
                assigned_hand_notes.append(assigned_note)
                active_notes_pitch.append(assigned_note[0])

    current_pitches = active_notes_pitch
    finger_positions = {p % 12 for p in current_pitches}
    min_pitch = min(current_pitches) if current_pitches else pitch
    max_pitch = max(current_pitches) if current_pitches else pitch

    state = {
        'fingers_used': len(finger_positions),
        'spread': max_pitch - min_pitch if current_pitches else 0,
        'min_pitch': min_pitch,
        'max_pitch': max_pitch
    }

    new_min = min(state['min_pitch'], pitch) if current_pitches else pitch
    new_max = max(state['max_pitch'], pitch) if current_pitches else pitch
    new_span = new_max - new_min

    span_cost = max(0, new_span - allowed_spread) ** 2
    finger_cost = 2.0 if (state['fingers_used'] >= max_fingers and 
                           (pitch % 12) not in {p % 12 for p in finger_positions}) else 0
    register_cost = 0.8 if (hand == 'left' and pitch >= 60) or (hand == 'right' and pitch < 60) else 0
    density_cost = 0.2 * len(current_pitches)

    return span_cost + finger_cost + register_cost + density_cost

# Load MIDI data from a file.
midi_data = PrettyMIDI('test.mid')

# Apply the clustering-based assignment with the refined mapping.
left_hand, right_hand = assign_notes_to_hands(midi_data, max_fingers=5, allowed_spread=8)

# Build a new PrettyMIDI object containing the two hands.
split_midi = PrettyMIDI()

# Create instruments for left and right hands.
left_instr = Instrument(program=0, name='Left Hand')   # left hand track
right_instr = Instrument(program=0, name='Right Hand')   # right hand track

# Add notes to their respective instruments.
for pitch, start, end, velocity in left_hand:
    note = Note(velocity=velocity, pitch=pitch, start=start, end=end)
    left_instr.notes.append(note)

for pitch, start, end, velocity in right_hand:
    note = Note(velocity=velocity, pitch=pitch, start=start, end=end)
    right_instr.notes.append(note)

split_midi.instruments.append(left_instr)
split_midi.instruments.append(right_instr)

# Write the separated parts to a new MIDI file.
split_midi.write('split_output.mid')

# Apply the dynamic programming assignment.
left_hand_dp, right_hand_dp = dynamic_programming_assign_hands(midi_data, max_fingers=5, allowed_spread=8)

# Build a new PrettyMIDI object containing the two hands (DP version).
split_midi_dp = PrettyMIDI()
left_instr_dp = Instrument(program=0, name='Left Hand DP')
right_instr_dp = Instrument(program=0, name='Right Hand DP')

for pitch, start, end, velocity in left_hand_dp:
    note = Note(velocity=velocity, pitch=pitch, start=start, end=end)
    left_instr_dp.notes.append(note)

for pitch, start, end, velocity in right_hand_dp:
    note = Note(velocity=velocity, pitch=pitch, start=start, end=end)
    right_instr_dp.notes.append(note)

split_midi_dp.instruments.append(left_instr_dp)
split_midi_dp.instruments.append(right_instr_dp)

# Write the separated parts to a new MIDI file (DP output).
split_midi_dp.write('split_output_dp.mid')
