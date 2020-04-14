from pyccs import Server


if __name__ == "__main__":
    server = Server(verify_names=False)
    print("We're up and away!")
    server.start()
