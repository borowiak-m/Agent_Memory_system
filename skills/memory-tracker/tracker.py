#!/usr/bin/env python3
# Memory Tracker - Tracks conversations for arbitrary entities
# Topics are separated: github_issues, shopify_products, etc.
# Each topic has its own index.json and topic_map.json

import json
import os
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path

MEMORY_BASE_DIR = "/home/dev/agents/memory"

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def read_json(path, default=None):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def get_topic_dir(topic):
    return f"{MEMORY_BASE_DIR}/{topic}"

#######################################
# Register a new topic
# Arguments:
#   topic - e.g., "github_issues", "shopify_products"
#   description - What this topic is for
#######################################
def register_topic(topic, description=""):
    topic_dir = get_topic_dir(topic)
    ensure_dir(f"{topic_dir}/active")
    ensure_dir(f"{topic_dir}/memory")
    
    config = {
        "topic": topic,
        "description": description,
        "created_at": now(),
        "active_count": 0,
        "memory_count": 0
    }
    write_json(f"{topic_dir}/config.json", config)
    write_json(f"{topic_dir}/index.json", [])
    write_json(f"{topic_dir}/topic_map.json", {})
    
    return {"status": "ok", "topic": topic, "message": "Topic registered"}

#######################################
# Start tracking a new entity in a topic
#######################################
def start_tracking(topic, entity_key, title=""):
    topic_dir = get_topic_dir(topic)
    active_dir = f"{topic_dir}/active/{entity_key}"
    
    if os.path.exists(active_dir):
        return {"status": "exists", "message": f"Entity {entity_key} is already being tracked"}
    
    if os.path.exists(f"{topic_dir}/memory/{entity_key}"):
        return {"status": "in_memory", "message": f"Entity {entity_key} exists in memory, reopen first"}
    
    ensure_dir(active_dir)
    
    manifest = {
        "topic": topic,
        "entity_key": entity_key,
        "title": title,
        "status": "active",
        "created_at": now(),
        "updated_at": now(),
        "message_count": 0
    }
    write_json(f"{active_dir}/manifest.json", manifest)
    write_json(f"{active_dir}/conversation.json", [])
    
    # Update topic counts
    config_path = f"{topic_dir}/config.json"
    config = read_json(config_path, {})
    config["active_count"] = len(os.listdir(f"{topic_dir}/active"))
    write_json(config_path, config)
    
    return {"status": "ok", "topic": topic, "entity_key": entity_key, "message": "Started tracking"}

#######################################
# Add a message to an active conversation
#######################################
def add_message(topic, entity_key, sender, content):
    active_dir = f"{get_topic_dir(topic)}/active/{entity_key}"
    
    if not os.path.exists(active_dir):
        return {"error": f"Entity {entity_key} is not being tracked"}
    
    conv_file = f"{active_dir}/conversation.json"
    manifest_file = f"{active_dir}/manifest.json"
    
    conversation = read_json(conv_file, [])
    conversation.append({
        "sender": sender,
        "content": content,
        "timestamp": now()
    })
    write_json(conv_file, conversation)
    
    manifest = read_json(manifest_file, {})
    manifest["message_count"] = len(conversation)
    manifest["updated_at"] = now()
    write_json(manifest_file, manifest)
    
    return {"status": "ok", "message": f"Message added to {topic}/{entity_key}"}

#######################################
# Close conversation and move to memory with summary
#######################################
def close_conversation(topic, entity_key, summary):
    topic_dir = get_topic_dir(topic)
    active_dir = f"{topic_dir}/active/{entity_key}"
    memory_dir = f"{topic_dir}/memory/{entity_key}"
    
    if not os.path.exists(active_dir):
        return {"error": f"Entity {entity_key} is not being tracked"}
    
    ensure_dir(memory_dir)
    
    # Move files
    manifest = read_json(f"{active_dir}/manifest.json", {})
    manifest["status"] = "closed"
    manifest["closed_at"] = now()
    manifest["summary"] = summary
    write_json(f"{memory_dir}/manifest.json", manifest)
    
    conversation = read_json(f"{active_dir}/conversation.json", [])
    write_json(f"{memory_dir}/conversation.json", conversation)
    
    # Move any other files
    for f in os.listdir(active_dir):
        if f not in ["manifest.json", "conversation.json"]:
            shutil.copy(f"{active_dir}/{f}", f"{memory_dir}/{f}")
    
    shutil.rmtree(active_dir)
    
    # Update topic index
    index = read_json(f"{topic_dir}/index.json", [])
    index.append({
        "entity_key": entity_key,
        "title": manifest.get("title", ""),
        "summary": summary,
        "closed_at": now(),
        "folder_path": memory_dir
    })
    write_json(f"{topic_dir}/index.json", index)
    
    # Update topic map
    topic_map = read_json(f"{topic_dir}/topic_map.json", {})
    topic_map[entity_key] = memory_dir
    write_json(f"{topic_dir}/topic_map.json", topic_map)
    
    # Update counts
    config = read_json(f"{topic_dir}/config.json", {})
    config["active_count"] = len(os.listdir(f"{topic_dir}/active"))
    config["memory_count"] = len(os.listdir(f"{topic_dir}/memory"))
    write_json(f"{topic_dir}/config.json", config)
    
    return {"status": "ok", "topic": topic, "entity_key": entity_key, "message": "Closed and archived to memory"}

#######################################
# Reopen a closed conversation from memory
#######################################
def reopen_conversation(topic, entity_key):
    topic_dir = get_topic_dir(topic)
    memory_dir = f"{topic_dir}/memory/{entity_key}"
    active_dir = f"{topic_dir}/active/{entity_key}"
    
    if not os.path.exists(memory_dir):
        return {"error": f"Entity {entity_key} not found in memory"}
    
    if os.path.exists(active_dir):
        return {"error": f"Entity {entity_key} is already active"}
    
    ensure_dir(active_dir)
    
    manifest = read_json(f"{memory_dir}/manifest.json", {})
    manifest["status"] = "active"
    manifest["reopened_at"] = now()
    for field in ["closed_at", "summary"]:
        if field in manifest:
            del manifest[field]
    write_json(f"{active_dir}/manifest.json", manifest)
    
    conversation = read_json(f"{memory_dir}/conversation.json", [])
    write_json(f"{active_dir}/conversation.json", conversation)
    
    shutil.rmtree(memory_dir)
    
    # Remove from index
    index = read_json(f"{topic_dir}/index.json", [])
    index = [i for i in index if i.get("entity_key") != entity_key]
    write_json(f"{topic_dir}/index.json", index)
    
    # Update topic map
    topic_map = read_json(f"{topic_dir}/topic_map.json", {})
    if entity_key in topic_map:
        del topic_map[entity_key]
    write_json(f"{topic_dir}/topic_map.json", topic_map)
    
    # Update counts
    config = read_json(f"{topic_dir}/config.json", {})
    config["active_count"] = len(os.listdir(f"{topic_dir}/active"))
    config["memory_count"] = len(os.listdir(f"{topic_dir}/memory"))
    write_json(f"{topic_dir}/config.json", config)
    
    return {"status": "ok", "topic": topic, "entity_key": entity_key, "message": "Reopened from memory"}

#######################################
# List topics
#######################################
def list_topics():
    topics = []
    if not os.path.exists(MEMORY_BASE_DIR):
        return []
    
    for name in os.listdir(MEMORY_BASE_DIR):
        topic_dir = f"{MEMORY_BASE_DIR}/{name}"
        if os.path.isdir(topic_dir):
            config_path = f"{topic_dir}/config.json"
            if os.path.exists(config_path):
                topics.append(read_json(config_path, {"topic": name}))
            else:
                topics.append({"topic": name, "description": "Legacy topic"})
    return topics

#######################################
# List active entities for a topic
#######################################
def list_active(topic):
    topic_dir = get_topic_dir(topic)
    if not os.path.exists(topic_dir):
        return {"error": f"Topic {topic} not found"}
    
    result = []
    active_dir = f"{topic_dir}/active"
    if os.path.exists(active_dir):
        for entity_key in os.listdir(active_dir):
            manifest_path = f"{active_dir}/{entity_key}/manifest.json"
            if os.path.isdir(f"{active_dir}/{entity_key}") and os.path.exists(manifest_path):
                manifest = read_json(manifest_path, {})
                manifest["entity_key"] = entity_key
                result.append(manifest)
    return result

#######################################
# List memory (archived) entities for a topic
#######################################
def list_memory(topic):
    topic_dir = get_topic_dir(topic)
    if not os.path.exists(topic_dir):
        return {"error": f"Topic {topic} not found"}
    
    result = []
    memory_dir = f"{topic_dir}/memory"
    if os.path.exists(memory_dir):
        for entity_key in os.listdir(memory_dir):
            manifest_path = f"{memory_dir}/{entity_key}/manifest.json"
            if os.path.isdir(f"{memory_dir}/{entity_key}") and os.path.exists(manifest_path):
                manifest = read_json(manifest_path, {})
                manifest["entity_key"] = entity_key
                result.append(manifest)
    return result

#######################################
# Get specific entity details
#######################################
def get_entity(topic, entity_key):
    topic_dir = get_topic_dir(topic)
    
    # Check active first
    active_dir = f"{topic_dir}/active/{entity_key}"
    if os.path.exists(active_dir):
        return {
            "status": "active",
            "entity_key": entity_key,
            "manifest": read_json(f"{active_dir}/manifest.json", {}),
            "conversation": read_json(f"{active_dir}/conversation.json", [])
        }
    
    # Check memory
    memory_dir = f"{topic_dir}/memory/{entity_key}"
    if os.path.exists(memory_dir):
        return {
            "status": "memory",
            "entity_key": entity_key,
            "manifest": read_json(f"{memory_dir}/manifest.json", {}),
            "conversation": read_json(f"{memory_dir}/conversation.json", [])
        }
    
    return {"error": f"Entity {entity_key} not found in topic {topic}"}

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    if cmd == "register":
        topic = sys.argv[2] if len(sys.argv) > 2 else ""
        description = sys.argv[3] if len(sys.argv) > 3 else ""
        print(json.dumps(register_topic(topic, description)))
    
    elif cmd == "start":
        topic = sys.argv[2] if len(sys.argv) > 2 else ""
        entity_key = sys.argv[3] if len(sys.argv) > 3 else ""
        title = sys.argv[4] if len(sys.argv) > 4 else ""
        print(json.dumps(start_tracking(topic, entity_key, title)))
    
    elif cmd == "add":
        topic = sys.argv[2] if len(sys.argv) > 2 else ""
        entity_key = sys.argv[3] if len(sys.argv) > 3 else ""
        sender = sys.argv[4] if len(sys.argv) > 4 else ""
        content = sys.argv[5] if len(sys.argv) > 5 else ""
        print(json.dumps(add_message(topic, entity_key, sender, content)))
    
    elif cmd == "close":
        topic = sys.argv[2] if len(sys.argv) > 2 else ""
        entity_key = sys.argv[3] if len(sys.argv) > 3 else ""
        summary = sys.argv[4] if len(sys.argv) > 4 else ""
        print(json.dumps(close_conversation(topic, entity_key, summary)))
    
    elif cmd == "reopen":
        topic = sys.argv[2] if len(sys.argv) > 2 else ""
        entity_key = sys.argv[3] if len(sys.argv) > 3 else ""
        print(json.dumps(reopen_conversation(topic, entity_key)))
    
    elif cmd == "list-topics":
        print(json.dumps(list_topics(), indent=2))
    
    elif cmd == "list-active":
        topic = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(list_active(topic), indent=2))
    
    elif cmd == "list-memory":
        topic = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(list_memory(topic), indent=2))
    
    elif cmd == "get":
        topic = sys.argv[2] if len(sys.argv) > 2 else ""
        entity_key = sys.argv[3] if len(sys.argv) > 3 else ""
        print(json.dumps(get_entity(topic, entity_key), indent=2))
    
    else:
        print("Memory Tracker - Topic-based conversation tracking")
        print("")
        print("Usage:")
        print("  python3 tracker.py register <topic> [description]")
        print("  python3 tracker.py start <topic> <entity_key> [title]")
        print("  python3 tracker.py add <topic> <entity_key> <sender> <content>")
        print("  python3 tracker.py close <topic> <entity_key> <summary>")
        print("  python3 tracker.py reopen <topic> <entity_key>")
        print("  python3 tracker.py list-topics")
        print("  python3 tracker.py list-active <topic>")
        print("  python3 tracker.py list-memory <topic>")
        print("  python3 tracker.py get <topic> <entity_key>")

if __name__ == "__main__":
    main()
