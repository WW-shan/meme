[View a markdown version of this page](shadow-tests.md)

# Shadow tests

With Amazon SageMaker AI you can evaluate any changes to your model serving infrastructure by comparing its performance
against the currently deployed infrastructure. This practice is known as shadow testing. Shadow testing can help
you catch potential configuration errors and performance issues before they impact end users. With SageMaker AI, you
don't need to invest in building your shadow testing infrastructure, so you can focus on model development.

You can use this capability to validate changes to any component of your production variant, namely the model,
the container, or the instance, without any end user impact. It is useful in situations including but not
limited to the following:

You are considering promoting a new model that has been validated offline to production, but want to
evaluate operational performance metrics such as latency and error rate before making this decision.

You are considering changes to your serving infrastructure container, such as patching vulnerabilities
or upgrading to newer versions, and want to assess the impact of these changes prior to promotion to
production.

You are considering changing your ML instance and want to evaluate how the new instance would perform
with live inference requests.

The SageMaker AI console provides a guided experience to manage the workflow of shadow testing. You can set up shadow
tests for a predefined duration of time, monitor the progress of the test through a live dashboard, clean up
upon completion, and act on the results. Select a production variant you want to test against, and SageMaker AI
automatically deploys the new variant in shadow mode and routes a copy of the inference requests to it in real
time within the same endpoint. Only the responses of the production variant are returned to the calling
application. You can choose to discard or log the responses of the shadow variant for offline comparison. For
more information on production and shadow variants, see [Validation of models in production](./model-validation.html).

See [Create a shadow test](./shadow-tests-create.html) for instructions on creating a
shadow test.

###### Note

Certain endpoint features may make your endpoint incompatible with shadow tests. If your
endpoint uses any of the following features, you cannot use shadow tests on your endpoint, and your request to
set up shadow tests will lead to validation errors.

Serverless inference

Asynchronous inference

Marketplace containers

Multiple-container endpoints

Multi-model endpoints

Endpoints that use Inf1 (Inferentia-based) instances

![Warning](https://d1ge0kk1l5kms0.cloudfront.net/images/G/01/webservices/console/warning.png) **Javascript is disabled or is unavailable in your browser.**

![Warning](https://d1ge0kk1l5kms0.cloudfront.net/images/G/01/webservices/console/warning.png)

To use the Amazon Web Services Documentation, Javascript must be enabled. Please refer to your browser's Help pages for instructions.

Thanks for letting us know we're doing a good job!

If you've got a moment, please tell us what we did right so we can do more of it.

Thanks for letting us know this page needs work. We're sorry we let you down.

If you've got a moment, please tell us how we can make the documentation better.
