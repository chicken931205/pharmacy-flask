import pandas as pd
from flasgger import swag_from
from flask import Blueprint, request, jsonify

from models import Product, db, Instruction
from models import User

api = Blueprint('api', __name__)


@api.route('/products', methods=['POST'])
@swag_from({
    'tags': ['Products'],
    'description': 'Add a new product along with its instructions',
    'parameters': [{
        'name': 'body',
        'description': 'Product object that needs to be added',
        'in': 'body',
        'schema': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'example': 'Product Name'},
                'price': {'type': 'number', 'format': 'float', 'example': 29.99},
                'instructions': {
                    'type': 'array',
                    'items': {'type': 'object', 'properties': {'step': {'type': 'string', 'example': 'Instruction 1'}}}
                }
            },
            'required': ['name', 'price', 'instructions']
        }
    }],
    'responses': {
        '200': {
            'description': 'Product added successfully',
            'schema': {'type': 'object', 'properties': {'id': {'type': 'integer', 'example': 1},
                                                        'name': {'type': 'string', 'example': 'Product Name'},
                                                        'price': {'type': 'number', 'format': 'float',
                                                                  'example': 29.99}, 'instructions': {'type': 'array',
                                                                                                      'items': {
                                                                                                          'type': 'object',
                                                                                                          'properties': {
                                                                                                              'step': {
                                                                                                                  'type': 'string',
                                                                                                                  'example': 'Instruction 1'}}}}}
                       },
            '400': {'description': 'Invalid input'}
        }
    }
})
def add_product():
    data = request.json
    try:
        name = data['name']
        price = data['price']
        instructions_data = data['instructions']

        product = Product(name=name, price=price)
        db.session.add(product)
        db.session.flush()
        instructions = [Instruction(step=step['step'], product_id=product.id) for step in instructions_data]
        db.session.add_all(instructions)
        db.session.commit()

        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'instructions': [{'step': inst.step} for inst in instructions]
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@api.route('/products/<int:product_id>', methods=['GET'])
@swag_from({
    'tags': ['Products'],
    'description': 'Get a product by ID',
    'parameters': [
        {'name': 'product_id', 'in': 'path', 'type': 'integer', 'description': 'ID of the product to fetch'}],
    'responses': {
        '200': {
            'description': 'Product details',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'example': 1},
                    'name': {'type': 'string', 'example': 'Product Name'},
                    'price': {'type': 'number', 'format': 'float', 'example': 29.99},
                    'instructions': {'type': 'array', 'items': {'type': 'object', 'properties': {
                        'step': {'type': 'string', 'example': 'Instruction 1'}}}}
                }
            }
        },
        '404': {'description': 'Product not found'}
    }
})
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    instructions = [{'step': inst.step} for inst in product.instructions]
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'instructions': instructions
    }), 200


@api.route('/products/<int:product_id>', methods=['PUT'])
@swag_from({
    'tags': ['Products'],
    'description': 'Update a product by ID',
    'parameters': [
        {
            'name': 'product_id',
            'in': 'path',
            'type': 'integer',
            'description': 'ID of the product to update',
            'required': True
        },
        {
            'name': 'body',
            'in': 'body',
            'description': 'Updated product object',
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'example': 'Updated Product Name'},
                    'price': {'type': 'number', 'format': 'float', 'example': 39.99},
                    'instructions': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {'step': {'type': 'string', 'example': 'Updated Instruction'}}
                        }
                    }
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Product updated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'example': 1},
                    'name': {'type': 'string', 'example': 'Updated Product Name'},
                    'price': {'type': 'number', 'format': 'float', 'example': 39.99},
                    'instructions': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {'step': {'type': 'string', 'example': 'Updated Instruction'}}
                        }
                    }
                }
            }
        },
        '404': {'description': 'Product not found'},
        '400': {'description': 'Invalid input'}
    }
})
def update_product(product_id):
    data = request.json
    product = Product.query.get(product_id)

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    try:
        if 'name' in data:
            product.name = data['name']
        if 'price' in data:
            product.price = data['price']
        if 'instructions' in data:
            # Delete existing instructions
            Instruction.query.filter_by(product_id=product.id).delete()
            # Add new instructions
            instructions = [Instruction(step=step['step'], product_id=product.id) for step in data['instructions']]
            db.session.add_all(instructions)

        db.session.commit()
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'instructions': [{'step': inst.step} for inst in instructions]
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@api.route('/products/<int:product_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Products'],
    'description': 'Delete a product by ID',
    'parameters': [
        {'name': 'product_id', 'in': 'path', 'type': 'integer', 'description': 'ID of the product to delete'}],
    'responses': {
        '200': {'description': 'Product deleted successfully'},
        '404': {'description': 'Product not found'}
    }
})
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@api.route('/products', methods=['GET'])
@swag_from({
    'tags': ['Products'],
    'description': 'Retrieve a list of all products',
    'responses': {
        '200': {
            'description': 'List of all products',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'example': 1},
                        'name': {'type': 'string', 'example': 'Product Name'},
                        'price': {'type': 'number', 'format': 'float', 'example': 29.99},
                        'instructions': {
                            'type': 'array',
                            'items': {'type': 'object',
                                      'properties': {'step': {'type': 'string', 'example': 'Instruction 1'}}}
                        }
                    }
                }
            }
        }
    }
})
def get_all_products():
    products = Product.query.all()
    result = []
    for product in products:
        instructions = [{'step': inst.step} for inst in product.instructions]
        result.append({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'instructions': instructions
        })
    return jsonify(result), 200


@api.route('/triggerBackup')
def triggerBackup():
    df = pd.read_csv('user.csv')
    payment_methods = {
        'starbucks_gift_card': 'Starbucks Gift Card',
        'e_transfer': 'E-Transfer',
        'amazon_gift_card': 'Amazon Gift Card',
        'tim_hortons_gift_card': "Tim Horton's Gift Card"
    }

    users = []
    for index, row in df.iterrows():
        user = User(
            full_name=row['full_name'],
            phone=row['pharmacy_phone'],
            pharmacy=row['pharmacy_name'],
            email=row['email'],
            password=row['password'],
            payment_method=payment_methods[row['payment_method']],
            generate_hash=False
        )
        users.append(user)

    try:
        db.session.add_all(users)
        db.session.commit()
    except Exception as e:
        db.session.rollback()

    return jsonify({'message': 'Successful'}), 200


@api.route('/updateUserFee')
def update_user_fee():
    try:
        users = User.query.all()
        for user in users:
            user.counselling_fee = sum(
                history.product.price for history in user.counselling_histories if not history.cashed_out
            )
            user.products_not_cashed_out = sum(
                1 for history in user.counselling_histories if not history.cashed_out
            )
            db.session.commit()
        return jsonify({'message': 'Successful'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
