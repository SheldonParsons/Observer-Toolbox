from core import generator


def main_testing():
    generator.start(["--info", "/Users/sheldon/Documents/GithubProject/Observer-Toolbox/report_info.yaml"])


def search_testing1():
    generator.start(["--get_products", "all", "--zendao_username", "a80646", "--zendao_password", "Woaini^6636865"])


def search_testing2():
    generator.start(["--get_projects", 150, "--zendao_username", "a80646", "--zendao_password", "Woaini^6636865"])


def search_testing3():
    generator.start(["--get_executions", 1058, "--zendao_username", "a80646", "--zendao_password", "Woaini^6636865"])


def search_testing4():
    generator.start(["--get_test_tasks", 150, "--zendao_username", "a80646", "--zendao_password", "Woaini^6636865"])


def search_testing5():
    generator.start(["--help"])


if __name__ == '__main__':
    main_testing()
