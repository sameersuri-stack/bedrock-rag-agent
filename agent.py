import boto3, json, re, urllib.parse, urllib.request

REGION = "ap-southeast-2"
KB_ID = "YOUR_KB_ID"
MODEL_ID = "apac.amazon.nova-lite-v1:0"

runtime = boto3.client("bedrock-runtime", region_name=REGION)
kb = boto3.client("bedrock-agent-runtime", region_name=REGION)


def get_json(url):
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def get_weather(city):
    geo = get_json("https://geocoding-api.open-meteo.com/v1/search"
                   f"?name={urllib.parse.quote(city)}&count=1")
    if not geo.get("results"):
        return {"error": f"City not found: {city}"}
    place = geo["results"][0]
    w = get_json("https://api.open-meteo.com/v1/forecast"
                 f"?latitude={place['latitude']}"
                 f"&longitude={place['longitude']}"
                 "&current=temperature_2m,wind_speed_10m")
    return {"city": place["name"], "country": place.get("country", ""),
            "weather": w["current"]}


def search_docs(query):
    r = kb.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration":
                                {"numberOfResults": 8}},
    )
    return {"chunks": [
        {"text": x["content"]["text"],
         "source": x["location"]["s3Location"]["uri"]}
        for x in r["retrievalResults"]]}


FUNCS = {"get_weather": get_weather, "search_docs": search_docs}

tools = {"tools": [
    {"toolSpec": {
        "name": "get_weather",
        "description": "Get the current weather for a city by its name, "
                       "for example 'Mumbai' or 'Tokyo'.",
        "inputSchema": {"json": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"]}}}},
    {"toolSpec": {
        "name": "search_docs",
        "description": "Search the user's PDFs about Jujutsu Kaisen, "
                       "Black Clover and Mob Psycho 100. Use SHORT keyword "
                       "queries like 'Gojo Satoru' and never repeat the "
                       "same query twice.",
        "inputSchema": {"json": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]}}}},
]}

SYSTEM = [{"text": "For ANY question about characters, people, stories "
                   "or series, you MUST call search_docs first and answer "
                   "ONLY from its results. Never use your own knowledge "
                   "for those. Use short keyword queries and never repeat "
                   "a query. If search_docs has nothing relevant, say the "
                   "documents don't contain it. For weather questions, "
                   "call get_weather with the city name immediately and "
                   "never ask the user for anything."}]


def chat(question):
    messages = [{"role": "user", "content": [{"text": question}]}]
    for _ in range(5):
        r = runtime.converse(modelId=MODEL_ID, messages=messages,
                             toolConfig=tools, system=SYSTEM)
        msg = r["output"]["message"]
        messages.append(msg)
        if r["stopReason"] != "tool_use":
            txt = "".join(b.get("text", "") for b in msg["content"])
            clean = re.sub(r"<thinking>.*?</thinking>", "", txt,
                           flags=re.S).strip()
            print(clean or re.sub(r"</?thinking>", "", txt).strip())
            return
        results = []
        for block in msg["content"]:
            if "toolUse" in block:
                t = block["toolUse"]
                print("Calling tool:", t["name"], t["input"])
                try:
                    data = FUNCS[t["name"]](**t["input"])
                except Exception as e:
                    data = {"error": str(e)}
                results.append({"toolResult": {
                    "toolUseId": t["toolUseId"],
                    "content": [{"json": data}]}})
        messages.append({"role": "user", "content": results})
    print("I couldn't find a clear answer in the documents.")


while True:
    q = input("\nAsk (or type quit): ").strip()
    if q.lower() in ("quit", "exit", "q"):
        break
    if q:
        chat(q)