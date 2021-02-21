import os
from types import resolve_bases
from flask import Flask, request, abort, jsonify
from sqlalchemy.sql.elements import Null
from sqlalchemy.sql.expression import false
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
  
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
    return response

  @app.route('/categories')
  def categories_list():
    categories = Category.query.order_by(Category.id).all()
    formatted_categories = [category.format()['type'] for category in categories]

    return jsonify({
      'success': True,
      'categories': formatted_categories
    })

  def paginate_questions(request, questions):
    page = request.args.get('page', 1, type=int)
    questions_json = [question.format() for question in questions]
    start_index = (page - 1)  * QUESTIONS_PER_PAGE
    end_index = start_index + QUESTIONS_PER_PAGE

    return questions_json[start_index:end_index]

  @app.route('/questions')
  def questions_list():
    categories = Category.query.order_by(Category.id).all()

    questions = Question.query.filter(Question.category==categories[0].id).order_by(Question.id).all()
    current_questions = paginate_questions(request, questions)

    if len(current_questions) == 0:
      abort(404)

    formatted_categories = [category.format()['type'] for category in categories]

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(questions),
      "categories": formatted_categories,
      "current_category": formatted_categories[0]
    })


  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):

    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'deleted': question_id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })

    except:
      abort(422)


  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()

    search_term = body.get('searchTerm', None)

    if search_term is not None:
      questions = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()

      current_questions = paginate_questions(request, questions)

      if len(current_questions) == 0:
        abort(404)

      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(questions)
      })

    
    new_answer = body.get('answer', None)
    new_question = body.get('question', None)
    new_category = body.get('category', None)
    new_difficulty = body.get('difficulty', None)

    try:
      question = Question(answer=new_answer, question=new_question
      , category=new_category, difficulty=new_difficulty)  
      question.insert()

      questions = Question.query.order_by(Question.id).all()

      current_questions = paginate_questions(request, questions)

      return jsonify({
      'success': True,
        'created': question.id,
        'questions': current_questions,
        'total_questions': len(questions)
      })

    except:
      abort(422)


  @app.route('/categories/<string:category_id>/questions')
  def category_qestions_list(category_id):
    questions = Question.query.filter(Question.category==category_id).order_by(Question.id).all()
    current_questions = paginate_questions(request, questions)

    current_category = Category.query.get(category_id)

    if current_category is not None:
      current_category = current_category.format()


    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(questions),
      'current_category': current_category 
      })
  
  @app.route('/quizzes', methods=['POST'])
  def quiz_questions():
    body = request.get_json()
    category_id = body.get('quiz_category', None)
    previous_questions = body.get('previous_questions', None)
    questions = Question.query.filter(Question.category==category_id['id'], Question.id.notin_(previous_questions)).all()

    index = random.randint(0, len(questions)-1)

    return jsonify({
      'success': True,
      'question': questions[index].format(),
      })

  @app.errorhandler(404)
  def not_found(erorr):
    return jsonify({
      "success":false,
      "erorr": 404,
      "message": "resourse not found"
    }), 404

  @app.errorhandler(422)
  def unprocessable(erorr):
    return jsonify({
      "success":false,
      "erorr": 422,
      "message": "unprocessable"
    }), 422


  return app

    