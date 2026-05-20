[![Quantitative Finance & Algo Trading Blog by QuantInsti](https://d1rwhvwstyk9gu.cloudfront.net/test/2019/05/current-QI.png)](https://www.quantinsti.com)



[Machine Learning](/tag/machine-learning/)  This Blog

# The Triple Barrier Method: A Python GPU-based computation

[Machine Learning](/tag/machine-learning/)

 8 min read

By[José Carlos Gonzáles Tanaka](https://www.linkedin.com/in/jos%C3%A9-carlos-gonz%C3%A1les-tanaka-60859284/)  
  
Whenever you start using a lot of data to backtest a strategy and you would like to use the triple-barrier method, you’ll face the issue of low time efficiency by running a CPU-based computation.

A course on [backtesting](https://quantra.quantinsti.com/course/backtesting-trading-strategies) can provide insights into handling large-scale data efficiently, equipping you with the skills to optimise backtesting processes and implement advanced methodologies in your trading strategies.

This article provides a great Nvidia-GPU-based solution code that you can implement and get much quicker the desired prediction feature. You can find the triple-barrier method code on [GitHub](https://github.com/quantra-go-algo/Algorithmic-Trading-Code-Examples/tree/main/blog_articles/risk-constrained-kelly-criterion) as well.

Quicker sounds great, doesn’t it? Let’s dive in!

* [What is the Triple-Barrier Method?](#what-is-the-triple-barrier-method)
* [Time Efficiency Limitations When Using the CPU](#time-efficiency-limitations-when-using-the-cpu)
* [Exploring the Synergy Between Rapids and Numba Libraries](#exploring-the-synergy-between-rapids-and-numba-libraries)
* [GPU compute hierarchy](#gpu-compute-hierarchy)
* [A GPU-based code to create the triple-barrier method prediction feature](#a-gpu-based-code-to-create-the-triple-barrier-method-prediction-feature)

---

## What is the Triple-Barrier Method?

The Triple-Barrier Method is a new tool in financial machine learning that offers a dynamic approach to creating a prediction feature based on [risk management](/trading-risk-management/). This method provides traders with a framework to set a prediction feature. It is based on what a trader would do if she set profit-taking and stop-loss levels that adapt in real-time to changing market conditions.

Unlike traditional trading strategies that use fixed percentages or arbitrary thresholds, the Triple-Barrier Method adjusts profit-taking and stop-loss levels based on price movements and market volatility. It achieves this by employing three distinct barriers around the trade entry point: the upper, lower, and vertical barriers. These barriers determine whether the signal will be long, short, or no position at all.

The upper barrier represents the profit-taking level, indicating when traders should consider closing their position to secure gains. On the other hand, the lower barrier serves as the stop-loss level, signalling when it's wise to exit the trade to limit potential losses.

What sets the Triple-Barrier Method apart is its incorporation of time through the vertical barrier. This time constraint ensures that profit-taking or stop-loss levels are reached within a specified timeframe; if not, the previous position is held for the next period. You can learn more about it in López de Prado’s (2018) book.

---

## Time Efficiency Limitations When Using the CPU

If you have 1 million price returns to convert into a classification-based prediction feature,  you’ll face time efficiency issues while using López de Prado’ (2018) algorithm. Let’s present some CPU limitations regarding that concern.

Time efficiency is an important factor in computing for tasks that range from basic calculations to sophisticated simulations and data processing. Central Processing Units (CPUs) are not without their limitations in terms of time efficiency, particularly when it comes to large-scale and highly parallelizable tasks. Let’s talk about CPU time efficiency constraints and how they affect different kinds of computations.

1. **Serial Processing:** One of the main drawbacks of CPUs is their intrinsic serial processing nature. Conventional CPUs are made to carry out instructions one after the other sequentially. Although this method works well for many tasks, it becomes inefficient when handling highly parallelizable tasks that would be better served by concurrent execution.
2. **Limited Parallelism:** CPUs usually have a finite number of cores, each of which can only handle one thread at a time. Even though modern CPUs come in a variety of core configurations (such as dual, quad, or more), their level of parallelism is still limited compared to other computing devices like GPUs or specialized hardware accelerators.
3. **Memory Bottlenecks:** Another drawback of CPUs is the potential for memory bottlenecks, particularly in tasks requiring frequent access to large datasets. CPUs have limited memory bandwidth, which can be saturated when processing large amounts of data or when several cores are vying for memory access simultaneously.
4. **Instruction-Level Parallelism (ILP) Constraints:** The term "instruction-level parallelism" (ILP) describes a CPU's capacity to carry out several instructions at once within one thread. The degree of parallelism that can be reached is naturally limited by hardware, resource constraints, and instruction dependencies.
5. **Context Switching Overhead:** Time efficiency may be impacted by context switching overhead, which is the process of preserving and regaining the state of a CPU's execution context when transferring between threads or processes. Even though efficient scheduling algorithms used in modern operating systems reduce context-switching overhead, it is still something to take into account, especially in multitasking environments.
6. **Mitigating Time Efficiency Limitations:** Although CPUs' time efficiency is naturally limited, there are several ways to get around these limitations and boost overall performance:
7. **Multi-Threading:** Apply multi-threading techniques to parallelize tasks and efficiently utilize the available CPU cores. Keep in mind potential overhead and contention issues when managing multiple threads. You’re better off using the maximum number of threads available per your CPU cores minus 1 to run your code efficiently.
8. **Optimized Algorithms:** Apply [data structures](/python-data-structures/) and algorithms specially designed to meet the needs of the given task. This could entail reducing pointless calculations, minimizing memory access patterns, and, when practical, taking advantage of parallelism.
9. **Distributed Computing:** Distribute computational tasks across several CPUs or servers in a distributed computing environment to take advantage of extra processing power and scale horizontally as needed.

**Is there another way?**  
Yes! Using a GPU. GPU is well-designed for parallelism. Here, we present the Nvidia-based solution.

---

## Exploring the Synergy Between Rapids and Numba Libraries

*New to GPU usage? New to Rapids? New to Numba?*  
Don’t worry! We've got you covered. Let’s dive into these topics.

When combined, Rapids and Numba, two great libraries in the Python ecosystem, provide a convincing way to speed up tasks involving data science and numerical computing. We'll go over the fundamentals of how these libraries interact and the advantages they offer computational workflows.

### Understanding Rapids

[Rapids library](/nvidia-gpu-rapids-libraries-trading/) is an open-source library suite that uses GPU acceleration to speed up machine learning and data processing tasks. Popular Python data science libraries, such as cuDF (GPU DataFrame), cuML (GPU Machine Learning), cuGraph (GPU Graph Analytics), and others, are available in GPU-accelerated versions thanks to Rapids, which is built on top of CUDA. Rapids significantly speeds up data processing tasks by utilizing the parallel processing power of GPUs. This allows analysts and data scientists to work with larger datasets and produce faster results.

### Understanding Numba

Numba is a just-in-time (JIT) Python compiler that optimizes machine code at runtime from [Python functions](/python-function-tutorial/). Numba is an optimization tool for numerical and scientific computing applications that makes Python code perform and compiled languages like C or Fortran. Developers can achieve significant performance gains for computationally demanding tasks by instructing Numba to compile Python functions into efficient machine code by annotating them with the **@cuda.jit decorator**.

### Synergy Between Rapids and Numba

Rapids and Numba work well together because of their complementary abilities to speed up numerical calculations. While Rapids is great at using GPU acceleration for data processing tasks, Numba uses JIT compilation to optimize Python functions to improve CPU-bound computation performance. Developers can use GPU acceleration for data-intensive tasks and maximize performance on CPU-bound computations by combining these [Python libraries](/python-trading-library/) to get the best of both worlds.

### How Rapids and Numba Work Together

The standard workflow when combining Rapids and Numba is to use Rapids to offload data processing tasks to GPUs and use Numba to optimize CPU-bound computations. This is how they collaborate:

Preprocessing Data with Rapids: To load, manipulate, and preprocess big datasets on the GPU, use the Rapids cuDF library. Utilize GPU-accelerated DataFrame operations to carry out tasks like filtering, joining, and aggregating data.

The Numba library offers a decorator called **@cuda.jit** that makes it possible to compile Python functions into CUDA kernels for NVIDIA GPU parallel execution. Conversely, RAPIDS is a CUDA-based open-source software library and framework suite. To speed up data processing pipelines from start to finish, it offers a selection of GPU-accelerated libraries for [data science](/steps-data-science/) and data analytics applications.

Various data processing tasks can be accelerated by using CUDA-enabled GPUs in conjunction with RAPIDS when @cuda.jit is used. For example, to perform computations on GPU arrays, you can write CUDA kernels using @cuda.jit (e.g., using [NumPy](/python-numpy-tutorial-installation-arrays-random-sampling/)-like syntax). These kernels can then be integrated into RAPIDS workflows for tasks like:

* [data preprocessing](/data-preprocessing/),
* [machine learning](/machine-learning-basics/), and
* [data visualization](/python-data-visualization-using-bokeh/).

---

## GPU compute hierarchy

Let’s understand how GPU’s hierarchy works. In GPU computing, particularly in frameworks like CUDA (Compute Unified Device Architecture) used by NVIDIA GPUs, these terms are fundamental to understanding parallel processing:

* **Thread:** A thread is the smallest unit of execution within a GPU. It's analogous to a single line of code executed in a traditional CPU. Threads are organized into groups called **warps** (in NVIDIA architecture) or **wavefronts** (in AMD architecture).
* **Block (or Thread Block):** A block is a group of threads that execute the same code in parallel. Threads within a block can share data through shared memory and synchronize their execution. The size of a block is limited by the GPU architecture and is typically a multiple of 32 threads (the warp size in NVIDIA GPUs).
* **Grid:** A grid is an assembly of blocks that share a common kernel or GPU function. It shows how the parallel computation is organized overall. Blocks in grids are frequently arranged along the x, y, and z axes, making them three-dimensional.

So, to summarize:

* Threads execute code.
* Threads are organized into blocks.
* Blocks are organized into grids.

---

## A GPU-based code to create the triple-barrier method prediction feature

I know you’ve been waiting for this algo! Here we present the code to create a prediction feature based on the triple-barrier method using GPU. Please take into consideration that we have used OHLC data. López de Prado (2018) uses another type of data. We have used Maks Ivanov (2019) code which is CPU-based.

Let’s explain stepwise:

### Step 1: Import Required Libraries

### Step 2: Define dropLabels Function

* This function drops labels from a dataset based on a minimum percentage threshold.
* It iteratively checks the occurrence of labels and drops those with insufficient examples until all labels meet the threshold.
* The function is based on López de Prado's (2018) book.

### Step 3: Define get\_Daily\_Volatility Function

* This function calculates the daily volatility of a given DataFrame.
* The function is based on López de Prado's (2018) book.

### Step 4: Define CUDA Kernel Function triple\_barrier\_method\_cuda

* This function is decorated with @cuda.jit to run on the GPU.
* It calculates various barriers for a triple barrier method trading strategy using CUDA parallelism. Here, we provide a modification of López de Prado’s (2018) book. We compute the vertical top and bottom barriers with the High and Close prices, too.
* It updates a CUDA array with barrier values.

### Step 5: Define triple\_barrier\_method Function

* This function prepares data and launches the CUDA kernel function triple\_barrier\_method\_cuda.
* It transforms the output CUDA array into a DataFrame.

### Step 6: Data Import and Preprocessing

* [Import](https://quantra.quantinsti.com/course/getting-market-data) stock data for Apple (AAPL) using Yahoo Finance API.
* Compute daily [volatility](https://quantra.quantinsti.com/glossary/Volatility).
* Drop rows with NaN values.

### Step 7: Obtain prediction feature

We will now obtain the prediction feature using the triple\_barrier\_method function

### Step 8: Labels’ counting Output

Output the value counts of the prediction feature

---

**References:**

* López de Prado, M. (2018). *Advances in financial machine learning*. John Wiley & Sons.
* Numba documentation. <https://numba.pydata.org/>
* Maks Ivanov (2019). *Financial Machine Learning Part 1: Labels*. Towards Data Science
* RAPIDS documentation. <https://rapids.ai/>

---

### Conclusion

Here, you have learned the basics of the triple-barrier method, the Rapids libraries, the Numba library, and how to create a prediction feature based on those things. Now, you might be asking yourself:

*What’s next?*  
*How could I profit from this prediction feature to create a strategy and go algo?* Well, you can use the prediction feature “y” in data for any supervised machine-learning-based strategy and see what you can get as trading performance!

Don’t know which ML model to use? Don’t worry! We've got you covered!  
You can learn from different models in this learning track by Quantra about [machine learning and deep learning in trading](https://quantra.quantinsti.com/learning-track/machine-learning-deep-learning-trading-1). Inside this learning track, you can find also this topic in detail within the [Feature Engineering](https://quantra.quantinsti.com/course/data-and-feature-engineering-for-trading) course we have.

Ready to trade? Get? Set? Go Algo!

---

**File in the download:**

* GPU-based code to create the triple-barrier method prediction feature - Python notebook

Login to Download

---

*Disclaimer: All investments and trading in the stock market involve risk. Any decision to place trades in the financial markets, including trading in stock or options or other financial instruments is a personal decision that should only be made after thorough research, including a personal risk and financial assessment and the engagement of professional assistance to the extent you believe necessary. The trading strategies or related information mentioned in this article is for informational purposes only.*

[![ML Models in Finance]()](https://quantra.quantinsti.com/learning-track/machine-learning-deep-learning-trading-1)

[ML Models in Finance](https://quantra.quantinsti.com/learning-track/machine-learning-deep-learning-trading-1)

##### Share Article:

#### [Jose Carlos Gonzales Tanaka](/author/jose/)

José Carlos is a Quantitative Researcher at QuantInsti who focuses on algorithmic trading and advanced analytics. He built a setup to trade forex using the Interactive Brokers API.

[![LinkedIn](/assets/images/common/LinkedIn-Icon.png)](https://www.linkedin.com/in/jose-carlos-gonzales-tanaka/ "Website: https://www.linkedin.com/in/jose-carlos-gonzales-tanaka/")

#### Covered Call Strategy Using Machine Learning

#### Forward Propagation In Neural Networks: Components and Applications

![Whatsapp Icon](/assets/images/common/whatsApp-icon.png)

Recieve updates over Whatsapp

×

Our cookie policy 

Our cookie policy

To give you the best user experience, through analytics, and to show you tailored & most relevant content on our website, we use cookies. Please note that by closing this banner, scrolling this page, clicking a link or continuing to use our site, you consent to our use of cookies. You can read more about our privacy policy [here](https://www.quantinsti.com/privacy-policy#privacyPolicy).

This website uses cookies to give you the best user experience. Enabling cookies allows us to show you tailored & most relevant content on our website. You can read more about our privacy policy [here](https://www.quantinsti.com/privacy-policy#privacyPolicy).

[Accept all cookies](javascript:;) [Accept only essential cookies](javascript:;)

 
