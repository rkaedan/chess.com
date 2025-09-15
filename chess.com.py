#!/usr/bin/env python3
"""
Web-based Chess Game with Flask
A drag-and-drop chess game similar to chess.com
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import chess
import chess.pgn
import json
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chess-game-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.move_history = []
        self.game_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def get_board_state(self):
        """Get current board state as a dictionary"""
        board_state = {}
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                square_name = chess.square_name(square)
                board_state[square_name] = {
                    'piece': piece.symbol(),
                    'color': 'white' if piece.color == chess.WHITE else 'black'
                }
        return board_state
    
    def get_legal_moves_from_square(self, square_name):
        """Get legal moves from a specific square"""
        try:
            square = chess.parse_square(square_name)
            legal_moves = []
            for move in self.board.legal_moves:
                if move.from_square == square:
                    legal_moves.append(chess.square_name(move.to_square))
            return legal_moves
        except:
            return []
    
    def make_move(self, from_square, to_square, promotion=None):
        """Attempt to make a move"""
        try:
            from_sq = chess.parse_square(from_square)
            to_sq = chess.parse_square(to_square)
            
            # Create move object
            move = chess.Move(from_sq, to_sq)
            
            # Handle pawn promotion
            if promotion and promotion.lower() in ['q', 'r', 'b', 'n']:
                promotion_pieces = {
                    'q': chess.QUEEN,
                    'r': chess.ROOK,
                    'b': chess.BISHOP,
                    'n': chess.KNIGHT
                }
                move = chess.Move(from_sq, to_sq, promotion=promotion_pieces[promotion.lower()])
            
            # Check if move is legal
            if move in self.board.legal_moves:
                # Get move in algebraic notation before making it
                move_san = self.board.san(move)
                self.board.push(move)
                self.move_history.append(move_san)
                return True, move_san
            else:
                return False, "Illegal move"
        except Exception as e:
            return False, str(e)
    
    def get_game_status(self):
        """Get current game status"""
        status = {
            'turn': 'white' if self.board.turn == chess.WHITE else 'black',
            'is_check': self.board.is_check(),
            'is_checkmate': self.board.is_checkmate(),
            'is_stalemate': self.board.is_stalemate(),
            'is_game_over': self.board.is_game_over(),
            'move_count': len(self.move_history),
            'last_move': self.move_history[-1] if self.move_history else None
        }
        
        if self.board.is_checkmate():
            winner = 'black' if self.board.turn == chess.WHITE else 'white'
            status['winner'] = winner
            status['result'] = f'{winner.title()} wins by checkmate!'
        elif self.board.is_stalemate():
            status['result'] = 'Draw by stalemate!'
        elif self.board.is_insufficient_material():
            status['result'] = 'Draw by insufficient material!'
        
        return status
    
    def undo_move(self):
        """Undo the last move"""
        if self.move_history:
            self.board.pop()
            self.move_history.pop()
            return True
        return False
    
    def reset_game(self):
        """Reset the game to initial state"""
        self.board = chess.Board()
        self.move_history = []
        self.game_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# Global game instance
game = WebChessGame()

@app.route('/')
def index():
    """Serve the main chess game page"""
    return render_template('chess.html')

@app.route('/api/board')
def get_board():
    """Get current board state"""
    return jsonify({
        'board': game.get_board_state(),
        'status': game.get_game_status()
    })

@app.route('/api/legal_moves/<square>')
def get_legal_moves(square):
    """Get legal moves from a square"""
    legal_moves = game.get_legal_moves_from_square(square)
    return jsonify({'legal_moves': legal_moves})

@app.route('/api/move', methods=['POST'])
def make_move():
    """Make a move"""
    data = request.get_json()
    from_square = data.get('from')
    to_square = data.get('to')
    promotion = data.get('promotion')
    
    success, message = game.make_move(from_square, to_square, promotion)
    
    response = {
        'success': success,
        'message': message,
        'board': game.get_board_state(),
        'status': game.get_game_status()
    }
    
    if success:
        # Emit move to all connected clients
        socketio.emit('move_made', response)
    
    return jsonify(response)

@app.route('/api/undo', methods=['POST'])
def undo_move():
    """Undo the last move"""
    success = game.undo_move()
    response = {
        'success': success,
        'board': game.get_board_state(),
        'status': game.get_game_status()
    }
    
    if success:
        socketio.emit('move_undone', response)
    
    return jsonify(response)

@app.route('/api/reset', methods=['POST'])
def reset_game():
    """Reset the game"""
    game.reset_game()
    response = {
        'success': True,
        'board': game.get_board_state(),
        'status': game.get_game_status()
    }
    
    socketio.emit('game_reset', response)
    return jsonify(response)

@app.route('/api/history')
def get_history():
    """Get move history"""
    return jsonify({'history': game.move_history})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {
        'board': game.get_board_state(),
        'status': game.get_game_status()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    # Ensure games directory exists
    Path("games").mkdir(exist_ok=True)
    
    # Run the Flask app
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, log_output=True)