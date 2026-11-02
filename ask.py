import boto3

REGION = "ap-southeast-2"
KB_ID = "YOUR_KB_ID"
MODEL_ARN = "arn:aws:bedrock:ap-southeast-2:YOUR_ACCOUNT_ID:inference profile/apac.amazon.nova-lite-v1:0"

client = boto3.client("bedrock-agent-runtime", region_name=REGION)

def ask(q):
    r = client.retrieve_and_generate(
        input={"text": q},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KB_ID,
                "modelArn": MODEL_ARN,
            },
        },
    )
    print(r["output"]["text"])
    for c in r.get("citations", []):
        for ref in c["retrievedReferences"]:
            print("source:", ref["location"]["s3Location"]["uri"])

while True: 
    q = input("\nAsk (or type quit):").strip()
    if q.lower() == in ("quit", "exit", "q"):
        break
    if q:
    ask(q)
