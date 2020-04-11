from pyccs import Server


if __name__ == "__main__":
    server = Server(verify_names=False)
    server.start()
    print("We're up and away!")