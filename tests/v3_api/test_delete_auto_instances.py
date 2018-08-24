from lib.aws import AmazonWebServices


def test_delete_automation_instances():
    filters = [
            {'Name': 'tag:Name', 'Values': ['testsa*', 'testcustom*']},
            {'Name': 'key-name', 'Values': ['jenkins-rke-validation']}]
    aws_nodes = AmazonWebServices().get_nodes(filters)
    AmazonWebServices().delete_nodes(aws_nodes)
