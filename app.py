from RESTServer import RESTServer

app = RESTServer()


@app.plugin
def cookie(request):
    pass


@app.plugin
def fuck(request):
    return "dasd"


@app.route('/fuck/:name/', methods=['POST', 'GET'])
def fuck(request, name):
    return {request.data.get('a'): name}


app.listen(8823)
