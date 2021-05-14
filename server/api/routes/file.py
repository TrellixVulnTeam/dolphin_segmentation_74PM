import celery.states as states

from flask import Blueprint, request, jsonify, current_app, url_for, make_response

file_api = Blueprint('file', __name__, url_prefix = "/file")

from api.services.validation.file import FileSelectValidator, FileListValidator, FilePathValidator
from api.services.content_type import ContentType
from api.services.serializer import Serializer

@file_api.route('/select', methods=['POST'])
def file_select():
    validator = FileSelectValidator()
    data = validator.validate(request)
    if data is None: return jsonify(validator.get_error_message()), 400 

    validator = FileListValidator()
    data = validator.validate(data)
    if data is None: return jsonify(validator.get_error_message()), 400 

    validator = FilePathValidator()
    data = validator.validate(data)
    if data is None: return jsonify(validator.get_error_message()), 400 

    task = current_app.config["FILE_WORKER"].send_task(f'{current_app.import_name}.process_file_select', args=[data], kwargs={})
    return jsonify({
        'url': f"{url_for('file.check_task_progress', task_id = task.id, external=True)}",
        'task_id': task.id
    })

@file_api.route('/download/<string:task_name>', defaults = {'format': 'csv'}, methods=['GET'])
@file_api.route('/download/<string:task_name>/<string:format>', methods=['GET'])
def file_download(task_name: str, format: str):
    content_type = ContentType()
    if not content_type.validate(format): return jsonify({"Error": "1", "Message": f"File format not supported: {format}."}), 400 
    serialised_data = current_app.config["CACHE"].get(f"processed_images_{task_name}")
    if serialised_data is None: return jsonify({"Error": "1", "Message": f"Data not found for task: {task_name}."}), 404 

    deserialised_data = Serializer().deserialize(serialised_data)
    data_file = content_type.convert_df(deserialised_data, format)
    res = make_response(data_file)
    res.headers["Content-Disposition"] = f"attachment; filename={task_name}.{format}"
    res.headers["Content-Type"] = content_type.get_content_type(format)
    return res

@file_api.route('/check_progress/<string:task_id>', methods=['GET'])
def check_task_progress(task_id: str):
    res = current_app.config["FILE_WORKER"].AsyncResult(task_id)
    if res.state == states.PENDING:
        return res.state
    else:
        return jsonify(res.result)
