import streamlit as st
import chess

st.set_page_config(page_title="Streamlit Chess", layout="wide")

# --- Helpers ---
def board_to_matrix(board):
    """Return 8x8 matrix of pieces or '.' """
    mat = []
    for rank in range(8):
        row = []
        for file in range(8):
            sq = chess.square(file, 7 - rank)
            p = board.piece_at(sq)
            row.append(p.symbol() if p else ".")
        mat.append(row)
    return mat

def square_name_from_rc(r, c):
    file = chr(ord("a") + c)
    rank = str(8 - r)
    return f"{file}{rank}"

def uci_move(from_sq, to_sq, promotion=None):
    m = from_sq + to_sq
    if promotion:
        m += promotion
    return m

# --- Session state ---
if "board" not in st.session_state:
    st.session_state.board = chess.Board()
if "selected" not in st.session_state:
    st.session_state.selected = None
if "legal_moves" not in st.session_state:
    st.session_state.legal_moves = []
if "history" not in st.session_state:
    st.session_state.history = []

board = st.session_state.board

# --- Sidebar ---
st.sidebar.title("Controls")
col1, col2 = st.sidebar.columns(2)
if col1.button("Undo"):
    if board.move_stack:
        board.pop()
        st.session_state.history.pop()
        st.session_state.selected = None
        st.session_state.legal_moves = []

if col2.button("Reset"):
    st.session_state.board = chess.Board()
    st.session_state.history = []
    st.session_state.selected = None
    st.session_state.legal_moves = []
    board = st.session_state.board

st.sidebar.write("**Turn:**", "White" if board.turn else "Black")
if board.is_check():
    st.sidebar.error("Check!")
if board.is_c_
