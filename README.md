# Software for Magnetic Susceptibility Measurement Station Using the AC Method

- **Author:** Marcin Zepp
- **Polish title:** Oprogramowanie stanowiska pomiarowego podatności magnetycznej metodą zmiennoprądową
- **Supervisor:** [dr hab. inż. Wojciech Tabiś, prof. AGH](https://orcid.org/0000-0002-8827-9944)
- **Affiliation:** [Superconducting and Magnetic Materials Group](https://galaxy.agh.edu.pl/~smm/), [Department of Solid State Physics](https://website.fis.agh.edu.pl/kfcs/), [Faculty of Physics and Applied Computer Science](https://www.fis.agh.edu.pl/), [AGH University of Krakow](https://www.agh.edu.pl/)
- **Field of study**: [Applied Computer Science](https://www.fis.agh.edu.pl/en/candidates/applied-computer-science)
- **Year**: 2026

## Project Description

This project aims to modernize the software for a custom-built measurement station dedicated to AC magnetic susceptibility studies, developed by the Superconducting and Magnetic Materials Group at AGH University of Krakow.

The old software operated only on Windows 95 and urgently needed an upgrade.

## Physics Background

The station consists of an external coil connected to a signal generator (lock-in amplifier), which outputs a sinusoidal signal of specified frequency and amplitude. Inside, two coils are wound in opposition. Inserting a magnetic material into one of them changes the induced EMF, producing a differential signal in the external coil - this is the (voltage-based) measure of magnetic susceptibility. The system measures how susceptibility varies with temperature, enabling precise determination of phase transitions. Temperature changes must be slow to minimize system inertia effects.

## Devices Supported

- **RS Pro Digital Multi-Meter RSDM3055A (USB-GPIB/SCPI)**
  - [Datasheet](https://eshop.micronix.sk/data/sk/att/004/9887-7134.pdf)
  - [Programming Guide](https://int.siglent.com/u_file/document/SDM%20Series%20Digital%20Multimeter_ProgrammingGuide_EN02A.pdf)
- **Lakeshore 330 Temperature Controller (GPIB)**
  - [Manual](https://www.lakeshore.com/docs/default-source/product-downloads/330_manual.pdf?sfvrsn=8bc1a8e1_1)
- **Stanford Research Lock-In Amplifier SR-830 (GPIB)**
  - [Manual](https://www.thinksrs.com/downloads/pdfs/manuals/SR830m.pdf)
