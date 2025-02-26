Mathematical Formulas in memories-dev
=====================================

This page demonstrates the mathematical formula rendering capabilities in the memories-dev documentation. The formulas are rendered using MathJax and enhanced with our custom formula enhancer component.

Basic Math Examples
-------------------

Inline math can be written using $x^2 + y^2 = z^2$ syntax, which renders as $x^2 + y^2 = z^2$. This is useful for including mathematical expressions within text.

Display math is written using the math directive:





.. math::
   

f(x) = \int_{-\infty}^{\infty} \hat{f}(\xi) e^{2\pi i \xi x} d\xi You can also use the align environment for multiple equations: 


.. math::
   

:nowrap: \begin{align} \nabla \times \vec{E} &= -\frac{\partial \vec{B}}{\partial t}\\ \nabla \times \vec{B} &= \mu_0 \vec{J} + \mu_0 \varepsilon_0 \frac{\partial \vec{E}}{\partial t}\\ \nabla \cdot \vec{E} &= \frac{\rho}{\varepsilon_0}\\ \nabla \cdot \vec{B} &= 0 \end{align} Earth Science Formulas --------------------- Here are some formulas commonly used in Earth science and remote sensing applications: Normalized Difference Vegetation Index (NDVI): 

.. math::
   

NDVI = \frac{NIR - Red}{NIR + Red} Where NIR is the near-infrared reflectance and Red is the red reflectance. Kriging Interpolation: 
.. math::
   

\hat{Z}(s_0) = \sum_{i=1}^{n} \lambda_i Z(s_i) Where: - $\hat{Z}(s_0)$ is the predicted value at location $s_0$ - $Z(s_i)$ is the observed value at location $s_i$ - $\lambda_i$ are the kriging weights The weights are determined by solving: .. math::
   :nowrap: \begin{align} \sum_{j = 1}^{n} \lambda_j \gamma(s_i, s_j) + \mu &= \gamma(s_i, s_0) \quad \text{for all } i\\ \sum_{i=1}^{n} \lambda_i &= 1 \end{align} Where $\gamma(s_i, s_j)$ is the semivariogram between locations $s_i$ and $s_j$. Climate Models - ------------ The energy balance model: .. math:: C \frac{dT}{dt} = S(1-\alpha) - \sigma T^4 + F Where: - $C$ is the heat capacity - $T$ is temperature - $S$ is the solar radiation - $\alpha$ is the albedo - $\sigma$ is the Stefan - Boltzmann constant - $F$ is the forcing term The advection - diffusion equation for atmospheric transport: .. math:: \frac{\partial C}{\partial t} + \vec{v} \cdot \nabla C = \nabla \cdot (D \nabla C) + S Where: - $C$ is the concentration - $\vec{v}$ is the velocity field - $D$ is the diffusion coefficient - $S$ is the source / sink term Machine Learning Formulas ------------------------ Loss function for neural networks: .. math:: L(\theta) = -\frac{1}{N} \sum_{i=1}^{N} \sum_{j=1}^{M} y_{ij} \log(p_{ij}) Where: - $\theta$ represents the model parameters - $N$ is the number of samples - $M$ is the number of classes - $y_{ij}$ is the true label (1 if sample i belongs to class j, 0 otherwise) - $p_{ij}$ is the predicted probability that sample i belongs to class j Gradient descent update rule: .. math:: \theta_{t + 1} = \theta_t - \eta \nabla_{\theta} L(\theta_t) Where: - $\theta_t$ are the parameters at iteration t - $\eta$ is the learning rate - $\nabla_{\theta} L(\theta_t)$ is the gradient of the loss function with respect to the parameters Complex Formulas - ------------- The Fourier transform: .. math:: \mathcal{F}[f(t)] = \hat{f}(\omega) = \int_{-\infty}^{\infty} f(t) e^{-i\omega t} dt And its inverse: .. math:: \mathcal{F}^{-1}[\hat{f}(\omega)] = f(t) = \frac{1}{2\pi} \int_{-\infty}^{\infty} \hat{f}(\omega) e^{i\omega t} d\omega The Navier-Stokes equations for incompressible flow: .. math:: :nowrap: \begin{align} \rho \left( \frac{\partial \vec{v}}{\partial t} + \vec{v} \cdot \nabla \vec{v} \right) &= -\nabla p + \mu \nabla^2 \vec{v} + \rho \vec{g}\\ \nabla \cdot \vec{v} &= 0 \end{align} Where: - $\rho$ is the density - $\vec{v}$ is the velocity field - $p$ is the pressure - $\mu$ is the dynamic viscosity - $\vec{g}$ is the gravitational acceleration Matrix Formulas - ------------ The determinant of a 3×3 matrix: .. math:: \det(A) = \begin{vmatrix} a_{11} & a_{12} & a_{13} \\ a_{21} & a_{22} & a_{23} \\ a_{31} & a_{32} & a_{33} \end{vmatrix} = a_{11} \begin{vmatrix} a_{22} & a_{23} \\ a_{32} & a_{33} \end{vmatrix} - a_{12} \begin{vmatrix} a_{21} & a_{23} \\ a_{31} & a_{33} \end{vmatrix} + a_{13} \begin{vmatrix} a_{21} & a_{22} \\ a_{31} & a_{32} \end{vmatrix} The eigenvalue problem: .. math:: A\vec{v} = \lambda \vec{v} Where: - $A$ is a square matrix - $\vec{v}$ is an eigenvector - $\lambda$ is an eigenvalue Conclusion --------- These examples demonstrate the formula rendering capabilities of the memories-dev documentation. The formulas are rendered using MathJax and enhanced with our custom formula enhancer component, which provides features such as: - Proper alignment and spacing - Formula numbering - Copy button for formulas - Responsive design for mobile devices - Improved accessibility
